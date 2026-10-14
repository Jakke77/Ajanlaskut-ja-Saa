"""Real Qt visibility and timers with an offline WebEngine substitute."""
import os
import unittest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QEvent, QObject, QUrl, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QSizePolicy, QWidget

from asaa.weather.providers import Place
from asaa.weather import windy_view


class FakeProfile(QObject):
    downloadRequested = pyqtSignal(object)

    def setHttpAcceptLanguage(self, language):
        self.language = language


class FakePage(QObject):
    permissionRequested = pyqtSignal(object)
    fullScreenRequested = pyqtSignal(object)

    def __init__(self, profile, view):
        super().__init__(view)
        self.profile = profile
        self.view = view
        self.scripts = []

    def setBackgroundColor(self, color):
        self.background = color

    def url(self):
        return QUrl(self.view.requests[-1] if self.view.requests else '')

    def runJavaScript(self, script, callback=None):
        self.scripts.append(script)
        if callback:
            callback({'state': 'fullscreen'})


class FakeSettings:
    def __init__(self):
        self.values = {}

    def setAttribute(self, attribute, value):
        self.values[attribute] = value


class FakeView(QWidget):
    loadStarted = pyqtSignal()
    loadFinished = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.requests = []
        self.request_sizes = []
        self.stops = 0
        self._settings = FakeSettings()
        self._zoom = 1.0

    def setPage(self, page):
        self.page = page

    def settings(self):
        return self._settings

    def setZoomFactor(self, zoom):
        self._zoom = zoom

    def zoomFactor(self):
        return self._zoom

    def load(self, url):
        self.requests.append(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))
        self.request_sizes.append((self.isVisible(), self.size()))
        self.loadStarted.emit()

    def stop(self):
        self.stops += 1
        self.loadFinished.emit(False)


class WindyViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.patches = [
            patch.object(windy_view, 'QWebEngineView', FakeView),
            patch.object(windy_view, 'QWebEngineProfile', FakeProfile),
            patch.object(windy_view, 'QWebEnginePage', FakePage),
        ]
        for replacement in self.patches:
            replacement.start()
        self.place = Place('Oulu', 65.0701, 25.5071)
        self.other_place = Place('Helsinki', 60.1699, 24.9384)
        self.widgets = []
        self.windy = self.create()
        self.web = self.windy.view

    def create(self, parent=None, **kwargs):
        widget = windy_view.WindyView(parent, **kwargs)
        widget.resize(640, 480)
        self.widgets.append(widget)
        return widget

    def tearDown(self):
        for widget in self.widgets:
            widget.stop()
            widget.hide()
            widget.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        for replacement in reversed(self.patches):
            replacement.stop()

    def events(self):
        self.app.processEvents()

    def show_and_load(self):
        self.windy.load(self.place, 9, 'temp')
        self.windy.show()
        self.events()

    def test_first_request_waits_until_visible_and_layout_has_run(self):
        self.windy.load(self.place, 9, 'temp')
        self.events()
        self.assertEqual(self.web.requests, [])
        self.windy.show()
        self.assertEqual(self.web.requests, [])
        self.events()
        self.assertEqual(self.web.requests, [windy_view.map_url(self.place, 9, 'temp')])
        visible, size = self.web.request_sizes[0]
        self.assertTrue(visible)
        self.assertGreater(size.width(), 500)
        self.assertGreater(size.height(), 300)

    def test_hidden_changes_load_only_the_latest_place_zoom_and_layer(self):
        self.windy.load(self.place, 9, 'temp')
        self.windy.load(self.other_place, 7, 'rain')
        self.windy.load(self.other_place, 5, 'wind')
        self.events()
        self.assertEqual(self.web.requests, [])
        self.windy.show()
        self.events()
        self.assertEqual(self.web.requests, [windy_view.map_url(self.other_place, 5, 'wind')])

    def test_same_active_or_successful_url_does_not_repeat_requests(self):
        self.show_and_load()
        for _ in range(3):
            self.windy.load(self.place, 9, 'temp')
            self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.web.loadFinished.emit(True)
        for _ in range(3):
            self.windy.setStyleSheet('background:#171720;')
            self.windy.load(self.place, 9, 'temp')
            self.events()
        self.windy.hide()
        self.windy.show()
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.assertFalse(self.windy.status.isVisible())
        self.assertFalse(self.windy.retry_button.isVisible())

    def test_failed_url_can_be_explicitly_requested_again(self):
        self.show_and_load()
        self.web.loadFinished.emit(False)
        self.assertTrue(self.windy.status.isVisible())
        self.assertTrue(self.windy.retry_button.isVisible())
        self.assertIn('ei latautunut', self.windy.status.text())
        self.assertTrue(self.windy.browser_button.isVisible())
        self.windy.load(self.place, 9, 'temp', force=True)
        self.events()
        self.assertEqual(len(self.web.requests), 2)
        self.assertFalse(self.windy.retry_button.isVisible())
        self.web.loadFinished.emit(True)
        self.assertFalse(self.windy.status.isVisible())

    def test_passive_failed_url_refresh_preserves_error_without_network_retry(self):
        self.show_and_load()
        self.web.loadFinished.emit(False)
        error = self.windy.status.text()
        for _ in range(3):
            self.windy.setStyleSheet('background:#171720;')
            self.windy.load(self.place, 9, 'temp')
            self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.assertEqual(self.windy.status.text(), error)
        self.assertTrue(self.windy.status.isVisible())
        self.assertTrue(self.windy.retry_button.isVisible())

    def test_failed_url_does_not_block_new_place_or_layer(self):
        self.show_and_load()
        self.web.loadFinished.emit(False)
        self.windy.load(self.other_place, 7, 'rain')
        self.events()
        self.assertEqual(len(self.web.requests), 2)
        self.assertEqual(self.web.requests[-1], windy_view.map_url(self.other_place, 7, 'rain'))

    def test_retry_button_reuses_existing_profile(self):
        self.show_and_load()
        profile = self.windy.profile
        self.web.loadFinished.emit(False)
        self.windy.retry_button.click()
        self.events()
        self.assertEqual(self.web.requests, [self.windy.url, self.windy.url])
        self.assertIs(self.windy.profile, profile)

    def test_showing_failed_view_retries_after_layout(self):
        self.show_and_load()
        self.web.loadFinished.emit(False)
        self.windy.hide()
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.windy.show()
        # Host pages sync their stored options immediately after showing.
        self.windy.load(self.place, 9, 'temp')
        self.assertEqual(len(self.web.requests), 1)
        self.events()
        self.assertEqual(len(self.web.requests), 2)

    def test_hiding_before_queued_load_cancels_timer_until_next_show(self):
        self.windy.load(self.place, 9, 'temp')
        self.windy.show()
        self.windy.hide()
        self.events()
        self.assertEqual(self.web.requests, [])
        self.windy.show()
        self.events()
        self.assertEqual(len(self.web.requests), 1)

    def test_force_reloads_successful_url_with_same_profile(self):
        self.show_and_load()
        profile = self.windy.profile
        self.web.loadFinished.emit(True)
        self.windy.load(self.place, 9, 'temp', force=True)
        self.events()
        self.assertEqual(self.web.requests, [self.windy.url, self.windy.url])
        self.assertIs(self.windy.profile, profile)

    def test_force_during_load_is_coalesced_and_starts_after_completion(self):
        self.show_and_load()
        self.windy.load(self.place, 9, 'temp', force=True)
        self.windy.load(self.place, 9, 'temp', force=True)
        self.windy.load(self.place, 9, 'temp')
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.web.loadFinished.emit(True)
        self.events()
        self.assertEqual(len(self.web.requests), 2)
        self.web.loadFinished.emit(True)
        self.events()
        self.assertEqual(len(self.web.requests), 2)

    def test_active_load_finishes_before_loading_latest_settings(self):
        self.show_and_load()
        self.windy.load(self.other_place, 7, 'rain')
        self.windy.load(self.other_place, 5, 'wind')
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.web.loadFinished.emit(False)
        self.events()
        self.assertEqual(self.web.requests[-1], windy_view.map_url(self.other_place, 5, 'wind'))
        self.assertEqual(len(self.web.requests), 2)
        self.web.loadFinished.emit(True)
        self.windy.load(self.other_place, 5, 'wind')
        self.events()
        self.assertEqual(len(self.web.requests), 2)

    def test_return_to_inflight_url_cancels_older_pending_change(self):
        self.show_and_load()
        self.windy.load(self.other_place, 7, 'rain')
        self.windy.load(self.place, 9, 'temp')
        self.web.loadFinished.emit(True)
        self.events()
        self.assertEqual(len(self.web.requests), 1)

    def test_finishing_hidden_view_does_not_load_pending_url_until_shown(self):
        self.show_and_load()
        self.windy.hide()
        self.windy.load(self.other_place, 7, 'rain')
        self.web.loadFinished.emit(True)
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.windy.show()
        self.events()
        self.assertEqual(self.web.requests[-1], windy_view.map_url(self.other_place, 7, 'rain'))
        self.assertEqual(len(self.web.requests), 2)

    def test_browser_action_uses_latest_url_and_never_opens_automatically(self):
        with patch.object(windy_view.QDesktopServices, 'openUrl') as open_url:
            self.show_and_load()
            self.web.loadFinished.emit(False)
            self.windy.load(self.other_place, 7, 'rain')
            self.events()
            open_url.assert_not_called()
            self.windy.browser_button.click()
            self.assertEqual(open_url.call_args.args[0].toString(QUrl.ComponentFormattingOption.FullyEncoded),
                windy_view.map_url(self.other_place, 7, 'rain'))

    def test_stop_cancels_queued_load_and_ignores_late_requests(self):
        self.windy.load(self.place, 9, 'temp')
        self.windy.show()
        self.windy.stop()
        self.windy.load(self.other_place, 7, 'rain', force=True)
        self.windy.retry()
        self.events()
        self.assertEqual(self.web.requests, [])
        self.assertIsNone(self.windy.view)
        self.assertFalse(self.windy.retry_button.isEnabled())

    def test_stop_during_load_ignores_completion_and_is_idempotent(self):
        self.show_and_load()
        self.windy.load(self.other_place, 5, 'wind', force=True)
        self.windy.stop()
        self.web.loadFinished.emit(True)
        self.windy.loaded(False)
        self.windy.stop()
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.assertEqual(self.web.stops, 1)
        self.assertIsNone(self.windy.view)

    def test_hidden_parent_also_defers_initial_request(self):
        parent = QWidget()
        child = self.create(parent)
        child.load(self.place, 9, 'temp')
        child.show()
        self.events()
        self.assertEqual(child.view.requests, [])
        parent.show()
        self.events()
        self.assertEqual(len(child.view.requests), 1)
        parent.hide()
        child.setParent(None)
        parent.deleteLater()

    def test_missing_webengine_has_informative_browser_fallback(self):
        with patch.object(windy_view, 'QWebEngineView', None):
            fallback = self.create()
        self.assertIsNone(fallback.view)
        self.assertIn('Qt WebEngine', '\n'.join(label.text() for label in fallback.findChildren(QLabel)))
        self.assertFalse(fallback.browser_button.isEnabled())
        fallback.load(self.place, 9, 'temp')
        fallback.show()
        self.events()
        self.assertTrue(fallback.browser_button.isVisible())
        self.assertTrue(fallback.browser_button.isEnabled())
        self.assertFalse(fallback.retry_button.isVisible())
        with patch.object(windy_view.QDesktopServices, 'openUrl') as open_url:
            fallback.browser_button.click()
            self.assertEqual(open_url.call_args.args[0].toString(QUrl.ComponentFormattingOption.FullyEncoded), fallback.url)

    def test_disabled_network_does_not_create_webengine(self):
        offline = self.create(network=False)
        offline.load(self.place, 9, 'temp')
        offline.show()
        self.events()
        self.assertIsNone(offline.view)
        self.assertIn('verkkohaku pois', '\n'.join(label.text() for label in offline.findChildren(QLabel)))

    def test_private_profile_keeps_permission_and_download_denials(self):
        self.assertEqual(self.windy.profile.language, 'fi-FI,fi;q=0.9,en;q=0.8')
        permission, download = Mock(), Mock()
        self.windy.page.permissionRequested.emit(permission)
        self.windy.profile.downloadRequested.emit(download)
        permission.deny.assert_called_once_with()
        download.cancel.assert_called_once_with()
        attributes = windy_view.QWebEngineSettings.WebAttribute
        self.assertFalse(self.web.settings().values[attributes.LocalContentCanAccessFileUrls])
        self.assertFalse(self.web.settings().values[attributes.FullScreenSupportEnabled])


if __name__ == '__main__':
    unittest.main()
