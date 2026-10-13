"""Exercise saved Windy selection and explicit refresh without external requests."""
from datetime import datetime, timedelta
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from asaa.app import Controller
from asaa.state import State
from asaa.weather.forecast import UTC
from asaa.weather.providers import Place
from asaa.weather.windy_view import map_url
from tests.test_icon_ui import MemoryIcons
from tests.test_wallpapers import MemoryBackend


class FakeWindy(QWidget):
    """A map surface records navigations, retaining successful same-URL loads."""
    def __init__(self, parent=None, *, network=True):
        super().__init__(parent)
        self.url = ''
        self.requests = []
        self.stopped = False
        self.pending = None

    def load(self, place, zoom, layer, *, force=False):
        url = map_url(place, zoom, layer)
        if url != self.url or force:
            self.url = url
            if self.isVisible():
                self.requests.append((url, force, True))
            else:
                self.pending = (url, force)

    def showEvent(self, event):
        super().showEvent(event)
        if self.pending:
            self.requests.append((*self.pending, True))
            self.pending = None

    def stop(self):
        self.stopped = True


class BusyWorker:
    def isRunning(self): return True


class WindyStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='asaa-windy-startup-')
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(os.environ, {'XDG_DATA_HOME': str(self.root/'data')})
        self.environment.start()
        self.main_map_patch = patch('asaa.ui.WindyView', FakeWindy)
        self.desktop_map_patch = patch('asaa.weather.widget.WindyView', FakeWindy)
        self.main_map_patch.start(); self.desktop_map_patch.start()
        self.controllers = []
        self.path = self.root/'state.json'

    def tearDown(self):
        for controller in reversed(self.controllers):
            self.dispose(controller)
        self.desktop_map_patch.stop(); self.main_map_patch.stop()
        self.environment.stop()
        self.temporary.cleanup()

    def dispose(self, controller):
        if controller.stopping: return
        controller.weather.worker = None
        controller.shutdown()
        controller.window.hide(); controller.window.deleteLater()
        for widget in controller.widgets.values():
            widget.hide(); widget.deleteLater()
        controller.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def start(self, *, desktop):
        if not self.path.exists():
            state = State(self.path)
            widgets = {key: False for key in state.settings['widgets']}
            widgets['weather'] = desktop
            state.configure({'provider': 'windy', 'widgets': widgets,
                             'place': {'name': 'Testipaikka', 'latitude': 60.2, 'longitude': 24.7},
                             'windy_zoom': 7, 'windy_layer': 'rain'})
        controller = Controller(self.app, State(self.path), network=False,
                                wallpaper_backend=MemoryBackend(), icon_backend=MemoryIcons())
        self.controllers.append(controller)
        controller.tick_timer.stop(); controller.weather.timer.stop(); controller.daily.timer.stop()
        controller.restore_widgets()
        controller.open_page('weather')
        self.app.processEvents()
        return controller, controller.window.page_widgets['weather']

    @staticmethod
    def allow_map_refresh(controller):
        # This exercises the enabled-map route while preventing any forecast
        # thread or remote request from being started by the test.
        controller.weather.network_enabled = True
        controller.weather.worker = BusyWorker()

    def test_saved_windy_selection_loads_after_two_starts_without_expansion(self):
        for desktop in (False, True):
            with self.subTest(desktop=desktop):
                self.path.unlink(missing_ok=True)
                controller, page = self.start(desktop=desktop)
                first_map = page.windy
                expected = map_url(controller.weather.place, 7, 'rain')
                self.assertIsNone(controller.weather.expanded)
                self.assertEqual(first_map.requests, [(expected, False, True)])
                self.assertIs(page.stack.currentWidget(), first_map)
                if desktop:
                    self.assertEqual(controller.weather.windy.requests, [(expected, False, True)])
                else:
                    self.assertIsNone(controller.weather.windy)
                self.dispose(controller)
                restarted, restarted_page = self.start(desktop=desktop)
                self.assertIsNot(restarted_page.windy, first_map)
                self.assertEqual(restarted_page.windy.requests, [(expected, False, True)])
                self.assertIsNone(restarted.weather.expanded)
                self.assertEqual(restarted.options['provider'], 'windy')
                self.dispose(restarted)

    def test_main_refresh_forces_both_visible_maps_during_forecast_fetch(self):
        controller, page = self.start(desktop=True)
        main_map, desktop_map = page.windy, controller.weather.windy
        main_map.requests.clear(); desktop_map.requests.clear()
        self.allow_map_refresh(controller)
        refresh = next(item for item in page.findChildren(QPushButton) if item.text() == 'Päivitä')
        refresh.click(); self.app.processEvents()
        expected = map_url(controller.weather.place, 7, 'rain')
        self.assertEqual(main_map.requests, [(expected, True, True)])
        self.assertEqual(desktop_map.requests, [(expected, True, True)])

    def test_explicit_refresh_does_not_create_a_hidden_desktop_map(self):
        controller, page = self.start(desktop=False)
        page.windy.requests.clear()
        self.allow_map_refresh(controller)
        controller.weather.refresh()
        self.assertEqual(len(page.windy.requests), 1)
        self.assertTrue(page.windy.requests[0][1])
        self.assertIsNone(controller.weather.windy)

    def test_refresh_leaves_hidden_main_map_untouched(self):
        controller, page = self.start(desktop=True)
        main_map, desktop_map = page.windy, controller.weather.windy
        main_map.requests.clear(); desktop_map.requests.clear()
        controller.open_page('overview'); self.app.processEvents()
        self.assertFalse(page.isVisible())
        self.allow_map_refresh(controller)
        controller.weather.refresh()
        self.assertEqual(main_map.requests, [])
        self.assertEqual(len(desktop_map.requests), 1)
        self.assertTrue(desktop_map.requests[0][1])

    def test_automatic_tick_and_font_change_retain_successful_maps(self):
        controller, page = self.start(desktop=True)
        main_map, desktop_map = page.windy, controller.weather.windy
        main_map.requests.clear(); desktop_map.requests.clear()
        self.allow_map_refresh(controller)
        controller.weather._last_fetch = datetime.now(UTC) - timedelta(days=1)
        controller.weather.tick(); self.app.processEvents()
        controller.configure({'font': 'DejaVu Sans'}); self.app.processEvents()
        self.assertEqual(main_map.requests, [])
        self.assertEqual(desktop_map.requests, [])

    def test_network_disabled_and_shutdown_skip_explicit_map_requests(self):
        controller, page = self.start(desktop=True)
        main_map, desktop_map = page.windy, controller.weather.windy
        main_map.requests.clear(); desktop_map.requests.clear()
        controller.weather.refresh()
        self.allow_map_refresh(controller)
        controller.weather.stopping = True
        controller.weather.refresh()
        self.assertEqual(main_map.requests, [])
        self.assertEqual(desktop_map.requests, [])

    def test_explicit_refresh_has_no_duplicate_base_map_reload(self):
        controller, page = self.start(desktop=True)
        main_map, desktop_map = page.windy, controller.weather.windy
        main_map.requests.clear(); desktop_map.requests.clear()
        controller.weather.network_enabled = True
        with patch('asaa.services.WeatherWidget.refresh') as forecast_refresh:
            controller.weather.refresh()
        forecast_refresh.assert_called_once_with(True)
        self.assertEqual(len(main_map.requests), 1)
        self.assertEqual(len(desktop_map.requests), 1)

    def test_place_and_settings_sync_preserve_selected_map_and_provider_exit(self):
        controller, page = self.start(desktop=False)
        changed_place = Place('Toinen paikka', 61.4, 23.8)
        controller.weather.set_place(changed_place)
        controller.configure({'windy_zoom': 11, 'windy_layer': 'wind'})
        self.assertEqual(page.windy.url, map_url(changed_place, 11, 'wind'))
        self.assertIs(page.stack.currentWidget(), page.windy)
        controller.weather.select_provider('yr')
        self.assertIs(page.stack.currentWidget(), page.forecast)


if __name__ == '__main__':
    unittest.main()
