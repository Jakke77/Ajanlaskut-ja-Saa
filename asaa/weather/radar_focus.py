"""Open official rain maps using their own unobstructed fullscreen control.

DOM fullscreen fills the WebEngine view; the Qt window remains a normal
window. The original provider chooses the map container and retains its
timeline, controls and attribution. Cookie choices stay with the user.
"""
from __future__ import annotations

import json
import math
import time

from PyQt6.QtCore import QObject, QEvent, QPointF, QTimer, QUrl, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication


_HOSTS = {'foreca': 'www.foreca.fi', 'fmi': 'www.ilmatieteenlaitos.fi'}
_PATHS = {'foreca': '/tutka', 'fmi': '/sadekartta'}


def official_document(provider, url):
    """Only the current official radar page may request contained fullscreen."""
    url = url if isinstance(url, QUrl) else QUrl(url)
    return (provider in _HOSTS and url.isValid() and url.scheme() == 'https'
            and url.host() == _HOSTS[provider] and url.port() in (-1, 443)
            and not url.userName() and not url.password()
            and url.path().rstrip('/') == _PATHS[provider])


def official_origin(provider, url):
    url = url if isinstance(url, QUrl) else QUrl(url)
    return (provider in _HOSTS and url.isValid() and url.scheme() == 'https'
            and url.host() == _HOSTS[provider] and url.port() in (-1, 443)
            and not url.userName() and not url.password())


# The FMI site's visible button enters fullscreen on its complete stage,
# including its legend/timeline. Its hidden native MapLibre button must not be
# clicked instead. Avoid build-specific Vue scope hashes.
PROBE_SCRIPT = r"""(() => {
  const provider = PROVIDER;
  const canvas = 'canvas.maplibregl-canvas';
  const visible = element => {
    const style = getComputedStyle(element), rect = element.getBoundingClientRect();
    return style.display !== 'none' && style.visibility === 'visible'
      && Number(style.opacity) !== 0 && rect.width > 0 && rect.height > 0;
  };
  const fullscreen = document.fullscreenElement;
  if (fullscreen) {
    return {state: fullscreen.querySelector(canvas) ? 'fullscreen' : 'wrong-fullscreen'};
  }
  // Keep the FMI consent choice at normal readable zoom. Test original
  // controls only; neither click them nor modify the site's consent state.
  if (provider === 'fmi') {
    const consent = [...document.querySelectorAll('button,[role="button"]')].some(b =>
      visible(b) && /^(salli (kaikki|vain välttämättömät)|hyväksy kaikki|accept all|allow only necessary)$/i
        .test(b.textContent.trim().replace(/\s+/g, ' ')));
    const dialog = [...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')]
      .some(d => visible(d) && /eväste|cookie/i.test(d.textContent));
    if (consent || dialog) return {state: 'consent'};
  }
  let button;
  if (provider === 'foreca') {
    button = [...document.querySelectorAll('button.maplibregl-ctrl-fullscreen')]
      .find(b => b.closest('.maplibregl-map')?.querySelector(canvas));
  } else {
    button = [...document.querySelectorAll('button[aria-label="Suurenna"][aria-pressed="false"]')]
      .find(b => {
        for (let stage = b.parentElement, n = 0; stage && n < 6;
             stage = stage.parentElement, n++) {
          if (stage.querySelector('.maplibregl-map ' + canvas)) return true;
        }
        return false;
      });
  }
  if (!button || button.disabled) return {state: 'missing'};
  const style = getComputedStyle(button);
  if (style.visibility !== 'visible' || style.display === 'none'
      || Number(style.opacity) === 0) return {state: 'missing'};
  button.scrollIntoView({block: 'center', inline: 'nearest'});
  const rect = button.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return {state: 'missing'};
  const x = rect.x + rect.width / 2, y = rect.y + rect.height / 2;
  const hit = document.elementFromPoint(x, y);
  if (!hit || (hit !== button && !button.contains(hit))) {
    if (provider === 'fmi' && hit?.closest('header,nav,[role="banner"],[role="navigation"]'))
      return {state: 'header-blocked'};
    return {state: 'blocked'};
  }
  return {state: 'ready', x, y};
})()"""


class RadarFocus(QObject):
    """Bounded, generation-safe adapter around the site's normal map button."""

    POLL_MS = 750
    MAX_POLLS = 80

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.provider = ''
        self.url = ''
        self.generation = 0
        self.active = False
        self._stopped = False
        self._busy = False
        self._polls = 0
        self._clicks = 0
        self._callback = None
        self._allow_fullscreen_until = 0.0
        self._ready = False
        self._fmi_staged = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._probe)
        self._deadline = QTimer(self)
        self._deadline.setSingleShot(True)
        self._deadline.timeout.connect(lambda: self._finish(False) if self.active else None)
        owner.page.fullScreenRequested.connect(self.fullscreen_requested)

    @staticmethod
    def supports(source):
        return source in (('foreca', 'map'), ('fmi', 'map'))

    def prepare(self, provider):
        """Allow Foreca's own desktop control to mount in a narrow widget."""
        if self.owner.view:
            view = self.owner.view
            view.setZoomFactor(self.viewport_zoom(provider,view.width(),view.height()))

    def viewport_zoom(self, provider, width, height):
        if provider == 'foreca':
            return max(0.25,min(1.0,max(1,width) / 600))
        if provider == 'fmi' and self._fmi_staged:
            # After the user's consent choice, a shallow widget can put the
            # native button behind the site's sticky navigation. Give the page
            # enough CSS height to reach its own button, then restore zoom 1.
            return max(0.25,min(1.0,max(1,width) / 600,max(1,height) / 500))
        return 1.0

    def begin(self, provider, url, callback):
        self.cancel()
        if self._stopped or not official_document(provider, url):
            return
        self.provider, self.url = provider, url
        self.active = True
        self._callback = callback
        self._polls = self._clicks = 0
        self.owner.status.setText('Avataan sadekarttaa…')
        self.owner.status.show()
        self._timer.start(0)
        self._deadline.start(self.POLL_MS * self.MAX_POLLS)

    def _current(self, generation=None):
        owner = self.owner
        return (not self._stopped and owner.view is not None and not owner._stopped
                and (generation is None or generation == self.generation)
                and owner.isVisible() and owner.url == self.url
                and owner._source == (self.provider, 'map')
                and owner._active_source == (self.provider, 'map')
                and official_document(self.provider, owner.page.url()))

    def _probe(self):
        if not self.active or self._busy:
            return
        if not self._current():
            if self.owner.isVisible():
                self._finish(False)
            return
        if self._polls >= self.MAX_POLLS:
            self._finish(False)
            return
        self._polls += 1
        self._busy = True
        generation = self.generation
        script = PROBE_SCRIPT.replace('PROVIDER', json.dumps(self.provider))
        self.owner.page.runJavaScript(script,
            lambda result: self._probed(result, generation))

    def _probed(self, result, generation):
        if generation != self.generation:
            return
        self._busy = False
        if not self.active or not self._current(generation):
            return
        state = result.get('state') if isinstance(result, dict) else None
        if state == 'fullscreen':
            self.owner.view.setZoomFactor(1.0)
            self._finish(True)
            return
        if state in ('blocked','consent'):
            self.owner.status.setText('Valitse sivuston evästeasetukset.')
            if state == 'consent' and self._fmi_staged:
                self._fmi_staged = False
                self.prepare('fmi')
        else:
            self.owner.status.setText('Avataan sadekarttaa…')
        if state == 'header-blocked' and self.provider == 'fmi':
            self._fmi_staged = True
            self.prepare('fmi')
        if state == 'ready' and self._clicks < 3:
            if self._click(result):
                self._clicks += 1
        self._timer.start(self.POLL_MS)

    def _click(self, result):
        # A JS .click() has no browser user activation. Send a normal Qt mouse
        # press/release to the actual visible control instead. Its normal site
        # event handler alone decides which container enters fullscreen.
        try:
            x, y = float(result['x']), float(result['y'])
        except (KeyError, TypeError, ValueError):
            return False
        view = self.owner.view
        zoom = view.zoomFactor()
        if not (math.isfinite(x) and math.isfinite(y)
                and 0 <= x * zoom < view.width() and 0 <= y * zoom < view.height()):
            return False
        point = QPointF(round(x * zoom), round(y * zoom))
        target = view.focusProxy() or view
        global_point = QPointF(target.mapToGlobal(point.toPoint()))
        self._allow_fullscreen_until = time.monotonic() + 5
        for event, buttons in ((QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton),
                               (QEvent.Type.MouseButtonRelease, Qt.MouseButton.NoButton)):
            QApplication.sendEvent(target, QMouseEvent(event, point, global_point,
                Qt.MouseButton.LeftButton, buttons, Qt.KeyboardModifier.NoModifier))
        return True

    def fullscreen_requested(self, request):
        if not request.toggleOn():
            # Exiting is always permitted, including cleanup after navigation.
            request.accept()
            if (self._ready and self._current()
                    and official_origin(self.provider, request.origin())):
                self._ready = False
                self.owner._radar_closed()
            return
        if (self._current() and time.monotonic() < self._allow_fullscreen_until
                and official_origin(self.provider, request.origin())):
            request.accept()
            self._fmi_staged = False
            self.owner.view.setZoomFactor(1.0)
        else:
            request.reject()
        self._allow_fullscreen_until = 0.0

    def _finish(self, ok):
        self.active = False
        self._busy = False
        self._ready = ok
        self._fmi_staged = False
        self._allow_fullscreen_until = 0.0
        self._timer.stop()
        self._deadline.stop()
        if not ok and self.provider == 'fmi':
            self.prepare('fmi')
        callback, self._callback = self._callback, None
        if callback:
            callback(ok)

    def cancel(self, *, exit_fullscreen=False):
        self.generation += 1
        self.active = self._busy = False
        self._ready = False
        self._fmi_staged = False
        self._allow_fullscreen_until = 0.0
        self._timer.stop()
        self._deadline.stop()
        self._callback = None
        if exit_fullscreen and self.owner.view and not self._stopped:
            self.owner.page.runJavaScript(
                'if (document.fullscreenElement) document.exitFullscreen();')

    def stop(self):
        self.cancel()
        self._stopped = True
