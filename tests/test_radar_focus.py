"""Exercise native Qt gestures and delayed WebEngine replies without network."""
import os
import unittest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QEvent, QUrl, Qt
from PyQt6.QtQml import QJSEngine
from PyQt6.QtWidgets import QApplication

from asaa.weather import windy_view
from asaa.weather.providers import Place
from asaa.weather.radar_focus import PROBE_SCRIPT, official_document, official_origin
from tests.test_windy_view import FakePage, FakeProfile, FakeView


class DeferredPage(FakePage):
    def __init__(self, profile, view):
        super().__init__(profile, view)
        self.callbacks = []
        self.document_url = None

    def url(self):
        return QUrl(self.document_url) if self.document_url is not None else super().url()

    def runJavaScript(self, script, callback=None):
        self.scripts.append(script)
        if callback:
            self.callbacks.append(callback)


class GestureView(FakeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gestures = []

    def mousePressEvent(self, event):
        self.gestures.append(('press', event.position(), event.button(), event.buttons()))

    def mouseReleaseEvent(self, event):
        self.gestures.append(('release', event.position(), event.button(), event.buttons()))


class RadarFocusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication(['radar-focus-tests'])

    def setUp(self):
        self.patches = [patch.object(windy_view, 'QWebEngineView', GestureView),
                        patch.object(windy_view, 'QWebEnginePage', DeferredPage),
                        patch.object(windy_view, 'QWebEngineProfile', FakeProfile)]
        for replacement in self.patches:
            replacement.start()
        self.place = Place('Oulu', 65.0701, 25.5071)
        self.widget = windy_view.WeatherWebView()
        self.widget.resize(640, 480)
        self.web, self.page, self.radar = self.widget.view, self.widget.page, self.widget._radar

    def tearDown(self):
        self.widget.stop()
        self.widget.hide()
        self.widget.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        for replacement in reversed(self.patches):
            replacement.stop()

    def load(self, provider='fmi'):
        self.widget.show()
        self.widget.load_source(provider, 'map', self.place)
        self.app.processEvents()
        self.web.loadFinished.emit(True)
        self.app.processEvents()
        self.assertTrue(self.page.callbacks)
        return self.page.callbacks.pop(0)

    def request(self, origin, on=True):
        request = Mock()
        request.toggleOn.return_value = on
        request.origin.return_value = QUrl(origin)
        self.page.fullScreenRequested.emit(request)
        return request

    def test_document_ready_does_not_mark_whole_website_as_ready(self):
        reply = self.load()
        self.assertTrue(self.radar.active)
        self.assertEqual(self.widget._loaded_url, '')
        self.assertEqual(self.widget._loading_url, self.widget.url)
        self.assertTrue(self.widget.status.isVisible())
        reply({'state': 'missing'})
        self.assertTrue(self.radar._timer.isActive())
        self.assertTrue(self.radar._deadline.isActive())
        self.radar._timer.stop()
        self.radar._probe()
        self.page.callbacks.pop(0)({'state': 'fullscreen'})
        self.assertFalse(self.radar.active)
        self.assertEqual(self.widget._loaded_url, self.widget.url)
        self.assertFalse(self.widget.status.isVisible())
        self.assertFalse(self.radar._deadline.isActive())

    def test_unobstructed_control_uses_native_mouse_press_release(self):
        reply = self.load()
        reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual([item[0] for item in self.web.gestures], ['press', 'release'])
        self.assertEqual(self.web.gestures[0][1].x(), 100)
        self.assertEqual(self.web.gestures[0][2:],
                         (Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton))
        self.assertEqual(self.web.gestures[1][3], Qt.MouseButton.NoButton)
        self.assertFalse(self.widget.isFullScreen())
        self.assertFalse(self.web.isFullScreen())
        self.assertFalse(any('.click(' in script for script in self.page.scripts))

    def test_cookie_overlay_never_receives_an_automatic_click(self):
        reply = self.load('foreca')
        reply({'state': 'blocked'})
        self.assertEqual(self.web.gestures, [])
        self.assertIn('Valitse sivuston evästeasetukset', self.widget.status.text())
        self.assertEqual(self.widget._loaded_url, '')
        self.radar._deadline.timeout.emit()
        self.assertFalse(self.radar.active)
        self.assertTrue(self.widget.retry_button.isVisible())
        self.assertIn('ei avautunut', self.widget.status.text())
        self.widget.retry_button.click()
        self.app.processEvents()
        self.assertEqual(len(self.web.requests), 2)

    def test_deadline_also_bounds_a_javascript_reply_that_never_arrives(self):
        reply = self.load()
        self.assertTrue(self.radar._busy)
        self.radar._deadline.timeout.emit()
        self.assertFalse(self.radar.active)
        self.assertEqual(self.widget._failed_url, self.widget.url)
        reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual(self.web.gestures, [])

    def test_only_current_official_map_origin_is_allowed_fullscreen(self):
        reply = self.load()
        unrequested = self.request('https://www.ilmatieteenlaitos.fi/')
        unrequested.reject.assert_called_once_with()
        reply({'state': 'ready', 'x': 100, 'y': 70})
        good = self.request('https://www.ilmatieteenlaitos.fi/')
        good.accept.assert_called_once_with()
        good.reject.assert_not_called()
        for origin in ('https://www.foreca.fi/', 'https://evil.test/',
                       'http://www.ilmatieteenlaitos.fi/',
                       'https://www.ilmatieteenlaitos.fi.evil.test/',
                       'https://www.ilmatieteenlaitos.fi:444/'):
            with self.subTest(origin=origin):
                self.radar._click({'x': 100, 'y': 70})
                bad = self.request(origin)
                bad.reject.assert_called_once_with()
                bad.accept.assert_not_called()
        self.widget.hide()
        hidden = self.request('https://www.ilmatieteenlaitos.fi/')
        hidden.reject.assert_called_once_with()
        exiting = self.request('https://evil.test/', on=False)
        exiting.accept.assert_called_once_with()

    def test_redirect_to_another_page_is_not_treated_as_the_official_radar(self):
        reply = self.load()
        self.page.document_url = 'https://www.ilmatieteenlaitos.fi/saa-ja-meri'
        bad = self.request('https://www.ilmatieteenlaitos.fi/')
        bad.reject.assert_called_once_with()
        reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual(self.web.gestures, [])
        self.radar._deadline.timeout.emit()
        self.assertEqual(self.widget._loaded_url, '')

    def test_source_change_invalidates_a_delayed_ready_control_reply(self):
        reply = self.load()
        old_generation = self.radar.generation
        self.widget.load_source('windy', 'graph', self.place)
        self.assertGreater(self.radar.generation, old_generation)
        reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual(self.web.gestures, [])
        self.app.processEvents()
        self.assertEqual(len(self.web.requests), 2)
        self.assertEqual(self.widget._active_source, ('windy', 'graph'))
        self.web.loadFinished.emit(True)
        self.assertEqual(self.widget._loaded_url, self.widget.url)
        bad = self.request('https://embed.windy.com/')
        bad.reject.assert_called_once_with()

    def test_place_change_while_focusing_uses_only_latest_map_coordinates(self):
        reply = self.load('foreca')
        self.widget.load_source('foreca', 'map', Place('Turku', 60.45, 22.27))
        self.app.processEvents()
        reply({'state': 'fullscreen'})
        self.assertEqual(self.widget._loaded_url, '')
        self.assertEqual(len(self.web.requests), 2)
        self.assertIn('lt=60.45', self.web.requests[-1])
        self.assertIn('ln=22.27', self.web.requests[-1])

    def test_refresh_queued_during_navigation_skips_focus_on_the_old_document(self):
        self.widget.show()
        self.widget.load_source('fmi', 'map', self.place)
        self.app.processEvents()
        self.widget.load_source('fmi', 'map', self.place, force=True)
        self.web.loadFinished.emit(True)
        self.app.processEvents()
        self.assertEqual(len(self.web.requests), 2)
        self.assertEqual(self.page.callbacks, [])
        self.web.loadFinished.emit(True)
        self.app.processEvents()
        self.assertTrue(self.radar.active)
        self.assertEqual(len(self.page.callbacks), 1)

    def test_hide_cancels_focus_then_show_resumes_without_an_extra_navigation(self):
        old_reply = self.load()
        self.widget.hide()
        self.assertFalse(self.radar._timer.isActive())
        self.assertFalse(self.radar._deadline.isActive())
        old_reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual(self.web.gestures, [])
        self.widget.show()
        self.app.processEvents()
        self.page.callbacks.pop(0)({'state': 'fullscreen'})
        self.assertEqual(len(self.web.requests), 1)
        self.assertEqual(self.widget._loaded_url, self.widget.url)

    def test_document_finishing_hidden_defers_focus_and_its_deadline_until_shown(self):
        self.widget.show()
        self.widget.load_source('fmi', 'map', self.place)
        self.app.processEvents()
        self.widget.hide()
        self.web.loadFinished.emit(True)
        self.app.processEvents()
        self.assertFalse(self.radar.active)
        self.assertFalse(self.radar._deadline.isActive())
        self.assertTrue(self.widget._document_ready)
        self.assertEqual(self.page.callbacks, [])
        self.widget.show()
        self.app.processEvents()
        self.assertTrue(self.radar.active)
        self.page.callbacks.pop(0)({'state': 'fullscreen'})
        self.assertEqual(len(self.web.requests), 1)
        self.assertEqual(self.widget._loaded_url, self.widget.url)

    def test_reopening_a_successful_map_checks_dom_fullscreen_without_reloading(self):
        self.load()({'state': 'fullscreen'})
        self.assertEqual(self.widget._loaded_url, self.widget.url)
        self.widget.hide()
        self.assertTrue(self.widget._document_ready)
        self.assertEqual(self.widget._loaded_url, '')
        self.widget.show()
        self.app.processEvents()
        self.page.callbacks.pop(0)({'state': 'fullscreen'})
        self.assertEqual(len(self.web.requests), 1)
        self.assertEqual(self.widget._loaded_url, self.widget.url)

    def test_user_exiting_fullscreen_does_not_leave_whole_website_marked_ready(self):
        self.load()({'state': 'fullscreen'})
        closed = self.request('https://www.ilmatieteenlaitos.fi/', on=False)
        closed.accept.assert_called_once_with()
        self.assertEqual(self.widget._loaded_url, '')
        self.assertEqual(self.widget._failed_url, self.widget.url)
        self.assertIn('suljettiin', self.widget.status.text())
        self.assertTrue(self.widget.retry_button.isVisible())
        self.widget.retry_button.click()
        self.app.processEvents()
        self.assertEqual(len(self.web.requests), 2)

    def test_stop_ignores_pending_replies_and_cancels_all_timers(self):
        reply = self.load()
        self.widget.stop()
        reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual(self.web.gestures, [])
        self.assertFalse(self.radar._timer.isActive())
        self.assertFalse(self.radar._deadline.isActive())
        self.assertIsNone(self.widget.view)

    def test_foreca_narrow_widget_exposes_the_sites_own_fullscreen_control(self):
        self.widget.resize(389, 189)
        reply = self.load('foreca')
        zoom = self.web.zoomFactor()
        self.assertLess(zoom, 1)
        self.assertGreaterEqual(self.web.width() / zoom, 590)
        reply({'state': 'ready', 'x': 100, 'y': 70})
        self.assertEqual(self.web.gestures[0][1].x(), round(100 * zoom))
        accepted = self.request('https://www.foreca.fi/')
        accepted.accept.assert_called_once_with()
        self.assertEqual(self.web.zoomFactor(), 1.0)

    def next_reply(self):
        self.radar._timer.stop()
        self.radar._probe()
        return self.page.callbacks.pop(0)

    def test_small_fmi_keeps_consent_readable_then_stages_only_a_blocking_header(self):
        self.widget.resize(389, 189)
        reply = self.load('fmi')
        self.assertEqual(self.web.zoomFactor(), 1.0)
        reply({'state': 'consent'})
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.assertEqual(self.web.gestures, [])
        self.next_reply()({'state': 'header-blocked'})
        zoom = self.web.zoomFactor()
        self.assertLess(zoom, 1.0)
        self.assertGreaterEqual(self.web.height() / zoom, min(500,self.web.height() / 0.25))
        self.assertEqual(self.web.gestures, [])
        self.widget._fit_forecast_viewport()
        self.assertEqual(self.web.zoomFactor(), zoom)
        self.next_reply()({'state': 'ready', 'x': 100, 'y': 140})
        self.assertEqual(self.web.gestures[0][1].y(), round(140 * zoom))
        requested = self.request('https://www.ilmatieteenlaitos.fi/')
        requested.accept.assert_called_once_with()
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.widget._fit_forecast_viewport()
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.next_reply()({'state': 'fullscreen'})
        self.assertEqual(self.widget._loaded_url, self.widget.url)

    def test_late_fmi_consent_restores_readable_zoom_without_choosing_anything(self):
        self.widget.resize(389, 189)
        self.load('fmi')({'state': 'header-blocked'})
        self.assertLess(self.web.zoomFactor(), 1.0)
        self.next_reply()({'state': 'consent'})
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.assertEqual(self.web.gestures, [])
        self.assertIn('evästeasetukset', self.widget.status.text())

    def test_fmi_header_staging_is_cleared_on_source_change_and_timeout(self):
        self.widget.resize(389, 189)
        self.load('fmi')({'state': 'header-blocked'})
        self.radar._deadline.timeout.emit()
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.assertFalse(self.radar._fmi_staged)
        self.widget.load_source('windy', 'map', self.place)
        self.assertEqual(self.web.zoomFactor(), 1.0)

    def test_actual_dom_probe_distinguishes_consent_header_and_other_overlays(self):
        # Run the exact production JavaScript against a tiny DOM fixture;
        # adapter-state mocks alone cannot verify the hit-test classification.
        engine = QJSEngine()
        setup = engine.evaluate(r"""
          var consentOpen = true, headerOverMap = true, otherOverlay = false;
          var scrolled = 0;
          const consent = {textContent: 'Salli vain välttämättömät',
            getBoundingClientRect: () => ({x:0,y:0,width:100,height:40})};
          const stage = {parentElement:null, querySelector: selector => ({canvas:true})};
          const button = {disabled:false, textContent:'', parentElement:stage,
            scrollIntoView: () => scrolled++,
            getBoundingClientRect: () => ({x:80,y:50,width:40,height:40}),
            contains: () => false};
          const header = {closest: () => ({tagName:'HEADER'})};
          const overlay = {closest: () => null};
          var document = {fullscreenElement:null,
            querySelectorAll: selector => selector === 'button,[role="button"]'
              ? (consentOpen ? [consent,button] : [button])
              : selector.includes('aria-label="Suurenna"') ? [button] : [],
            elementFromPoint: () => otherOverlay ? overlay : headerOverMap ? header : button};
          var getComputedStyle = element => ({display:'block',visibility:'visible',opacity:'1'});
        """)
        self.assertFalse(setup.isError(), setup.toString())
        script = PROBE_SCRIPT.replace('PROVIDER', '"fmi"')
        result = engine.evaluate(script)
        self.assertFalse(result.isError(), result.toString())
        self.assertEqual(result.toVariant(), {'state': 'consent'})
        self.assertEqual(engine.evaluate('scrolled').toInt(), 0)
        engine.evaluate('consentOpen = false;')
        self.assertEqual(engine.evaluate(script).toVariant(), {'state': 'header-blocked'})
        engine.evaluate('otherOverlay = true;')
        self.assertEqual(engine.evaluate(script).toVariant(), {'state': 'blocked'})
        engine.evaluate('otherOverlay = false; headerOverMap = false;')
        self.assertEqual(engine.evaluate(script).toVariant(), {'state': 'ready', 'x': 100, 'y': 70})

    def test_invalid_control_coordinates_are_never_clicked(self):
        self.load()
        for coordinates in ((-1, 20), (20, -1), (100000, 20), (float('nan'), 20),
                            (20, float('inf')), ('bad', 20)):
            self.assertFalse(self.radar._click(dict(zip(('x', 'y'), coordinates))))
        self.assertEqual(self.web.gestures, [])

    def test_ordinary_map_data_still_preserves_browser_permissions_and_download_denial(self):
        permission, download = Mock(), Mock()
        self.page.permissionRequested.emit(permission)
        self.widget.profile.downloadRequested.emit(download)
        permission.deny.assert_called_once_with()
        download.cancel.assert_called_once_with()

    def test_fullscreen_support_is_limited_to_foreca_and_fmi_radar(self):
        flag = windy_view.QWebEngineSettings.WebAttribute.FullScreenSupportEnabled
        self.assertFalse(self.web.settings().values[flag])
        for provider, mode, enabled in (('foreca', 'map', True), ('fmi', 'map', True),
                                       ('windy', 'graph', False), ('windy', 'map', False)):
            self.widget.load_source(provider, mode, self.place)
            self.assertEqual(self.web.settings().values[flag], enabled)
        self.widget.load_source('foreca', 'map', self.place)
        self.widget.load(self.place, 9, 'rain')
        self.assertFalse(self.web.settings().values[flag])

    def test_document_and_origin_allowlists_do_not_accept_near_matches(self):
        self.assertTrue(official_document('foreca', 'https://www.foreca.fi/tutka?lt=65'))
        self.assertTrue(official_document('fmi', 'https://www.ilmatieteenlaitos.fi/sadekartta/'))
        self.assertTrue(official_origin('fmi', 'https://www.ilmatieteenlaitos.fi'))
        for url in ('https://foreca.fi/tutka', 'https://www.foreca.fi/kartta-v2',
                    'https://www.foreca.fi/tutka/elsewhere',
                    'https://user@www.foreca.fi/tutka', 'http://www.foreca.fi/tutka',
                    'https://www.foreca.fi.evil.test/tutka'):
            with self.subTest(url=url):
                self.assertFalse(official_document('foreca', url))


if __name__ == '__main__':
    unittest.main()
