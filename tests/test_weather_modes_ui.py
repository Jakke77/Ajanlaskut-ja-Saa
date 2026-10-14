"""Saved provider views and visible UI navigation without external requests."""
import copy
from datetime import date
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication, QWidget

from asaa.app import Controller
from asaa.state import DEFAULTS, State, atomic_json
from asaa.weather.providers import Place
from asaa.weather.web_sources import FMI_RADAR_URL, forecast_url, source_url
from tests.test_icon_ui import MemoryIcons
from tests.test_wallpapers import MemoryBackend
from tests.test_windy_startup import BusyWorker, FakeWindy


class WeatherViewStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='asaa-weather-modes-state-')
        self.path = Path(self.temporary.name)/'state.json'
        self.state = State(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_legacy_state_retains_native_graphs_and_windy_map(self):
        for provider in DEFAULTS['weather_views']:
            with self.subTest(provider=provider):
                old = copy.deepcopy(self.state.data)
                old['settings']['provider'] = provider
                old['settings'].pop('weather_views')
                old['notes']['2026-10-07'] = 'Säilyvä merkintä'
                atomic_json(self.path, old)
                loaded = State(self.path)
                self.assertEqual(loaded.settings['provider'], provider)
                self.assertEqual(loaded.settings['weather_views'], DEFAULTS['weather_views'])
                self.assertEqual(loaded.note(date(2026, 10, 7)), 'Säilyvä merkintä')

    def test_missing_provider_entries_receive_defaults_without_losing_modes(self):
        old = copy.deepcopy(self.state.data)
        old['settings']['weather_views'] = {'fmi': 'map', 'windy': 'graph'}
        atomic_json(self.path, old)
        loaded = State(self.path)
        self.assertEqual(loaded.settings['weather_views'],
                         {'yr': 'graph', 'foreca': 'graph', 'fmi': 'map', 'windy': 'graph'})
        loaded.configure({'opacity': 90})
        self.assertEqual(State(self.path).settings['weather_views'], loaded.settings['weather_views'])

    def test_invalid_mode_changes_leave_memory_and_saved_file_unchanged(self):
        self.state.configure({'weather_views': {**DEFAULTS['weather_views'], 'foreca': 'map'}})
        before = copy.deepcopy(self.state.data)
        saved = self.path.read_bytes()
        for views in (None, [], {'foreca': 'map'},
                      {**DEFAULTS['weather_views'], 'unknown': 'graph'},
                      {**DEFAULTS['weather_views'], 'yr': 'map'},
                      {**DEFAULTS['weather_views'], 'fmi': 'satellite'},
                      {**DEFAULTS['weather_views'], 'windy': []}):
            with self.subTest(views=views):
                with self.assertRaises(ValueError): self.state.configure({'weather_views': views})
                self.assertEqual(self.state.data, before)
                self.assertEqual(self.path.read_bytes(), saved)

    def test_malformed_saved_view_setting_is_rejected(self):
        old = copy.deepcopy(self.state.data)
        old['settings']['weather_views'] = 'map'
        atomic_json(self.path, old)
        with self.assertRaises(ValueError): State(self.path)


class FakeWeatherWeb(QWidget):
    def __init__(self, parent=None, *, network=True):
        super().__init__(parent)
        self.url = ''
        self.requests = []
        self.stopped = False
        self.pending = None

    def load_source(self, provider, mode, place, zoom=9, layer='temp', foreca_url='', *, force=False):
        url = source_url(provider, mode, place, zoom, layer, foreca_url)
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


class WeatherModeUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='asaa-weather-modes-ui-')
        self.root = Path(self.temporary.name)
        self.patches = [patch.dict(os.environ, {'XDG_DATA_HOME': str(self.root/'data')}),
                        patch('asaa.ui.WindyView', FakeWindy),
                        patch('asaa.ui.WeatherWebView', FakeWeatherWeb),
                        patch('asaa.weather.widget.WindyView', FakeWindy),
                        patch('asaa.weather.widget.WeatherWebView', FakeWeatherWeb)]
        for replacement in self.patches: replacement.start()
        self.controllers = []
        self.path = self.root/'state.json'

    def tearDown(self):
        for controller in reversed(self.controllers): self.dispose(controller)
        for replacement in reversed(self.patches): replacement.stop()
        self.temporary.cleanup()

    def dispose(self, controller):
        if controller.stopping: return
        controller.weather.worker = None
        controller.shutdown()
        controller.window.hide(); controller.window.deleteLater()
        for widget in controller.widgets.values(): widget.hide(); widget.deleteLater()
        controller.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def start(self, *, desktop=True, open_weather=True):
        if not self.path.exists():
            state = State(self.path)
            widgets = {key: False for key in state.settings['widgets']}
            widgets['weather'] = desktop
            state.configure({'widgets': widgets})
        controller = Controller(self.app, State(self.path), network=False,
                                wallpaper_backend=MemoryBackend(), icon_backend=MemoryIcons())
        self.controllers.append(controller)
        controller.tick_timer.stop(); controller.weather.timer.stop(); controller.daily.timer.stop()
        controller.restore_widgets()
        controller.open_page('weather' if open_weather else 'overview')
        self.app.processEvents()
        return controller, controller.window.page_widgets['weather']

    def choose(self, control, value):
        control.setCurrentIndex(control.findData(value)); self.app.processEvents()

    def test_provider_specific_modes_are_shared_and_remembered_across_restart(self):
        controller, page = self.start()
        self.assertIs(page.stack.currentWidget(), page.forecast)
        self.choose(page.view, 'map')
        self.assertEqual(controller.weather.view_mode, 'map')
        self.assertIs(page.stack.currentWidget(), page.weather_web)
        self.assertTrue(controller.weather.web_view.isVisible())
        self.choose(page.provider, 'fmi')
        self.assertEqual(controller.weather.view_mode, 'graph')
        self.choose(page.view, 'map')
        self.assertEqual(page.weather_web.url, FMI_RADAR_URL)
        self.assertEqual(controller.weather.web_view.url, FMI_RADAR_URL)
        self.choose(page.provider, 'foreca')
        self.assertEqual(page.view.currentData(), 'map')
        controller.weather.set_view_mode('graph')
        self.assertEqual(page.view.currentData(), 'graph')
        self.assertIs(page.stack.currentWidget(), page.forecast)
        self.choose(page.provider, 'fmi')
        self.dispose(controller)
        restarted, new_page = self.start()
        self.assertEqual(restarted.weather.selected, 'fmi')
        self.assertEqual(new_page.view.currentData(), 'map')
        self.assertIs(new_page.stack.currentWidget(), new_page.weather_web)
        self.assertEqual(new_page.weather_web.requests, [(FMI_RADAR_URL, False, True)])

    def test_windy_hourly_view_uses_own_forecast_and_preserves_native_hour_choice(self):
        controller, page = self.start()
        self.choose(page.count, 12)
        self.choose(page.provider, 'windy')
        self.assertIs(page.stack.currentWidget(), page.windy)
        self.choose(page.view, 'graph')
        self.assertEqual(page.view.currentText(), 'Tuntiennuste')
        self.assertFalse(page.count.isEnabled())
        self.assertIs(page.stack.currentWidget(), page.weather_web)
        self.assertEqual(page.weather_web.url, forecast_url(controller.weather.place))
        self.assertEqual(controller.weather.forecast, None)
        self.choose(page.provider, 'yr')
        self.assertEqual(page.view.count(), 1)
        self.assertFalse(page.view.isEnabled())
        self.assertTrue(page.count.isEnabled())
        self.assertEqual(page.forecast.count, 12)
        self.assertIs(page.stack.currentWidget(), page.forecast)

    def test_foreca_map_uses_cached_resolved_city_without_guessing_place_name(self):
        controller, page = self.start(desktop=False)
        with patch.object(controller.weather.caches['foreca'], 'read',
                          return_value={'source_url': 'https://www.foreca.fi/Finland/Tampere/hourly'}):
            self.choose(page.view, 'map')
        self.assertEqual(page.weather_web.url, 'https://www.foreca.fi/Finland/Tampere/kartta-v2')
        self.assertTrue(all(request[2] for request in page.weather_web.requests))

    def test_saved_radar_does_not_create_hidden_web_surfaces(self):
        state = State(self.path)
        widgets = {key: False for key in state.settings['widgets']}
        state.configure({'provider': 'fmi', 'widgets': widgets,
                         'weather_views': {**DEFAULTS['weather_views'], 'fmi': 'map'}})
        controller, page = self.start(desktop=False, open_weather=False)
        self.assertIsNone(page.weather_web)
        self.assertIsNone(controller.weather.weather_web)
        controller.open_page('weather'); self.app.processEvents()
        self.assertEqual(page.weather_web.requests, [(FMI_RADAR_URL, False, True)])
        self.assertIsNone(controller.weather.weather_web)

    def test_manual_radar_refresh_recovers_visible_views_during_busy_forecast_fetch(self):
        controller, page = self.start()
        self.choose(page.provider, 'fmi'); self.choose(page.view, 'map')
        main, desktop = page.weather_web, controller.weather.web_view
        main.requests.clear(); desktop.requests.clear()
        controller.weather.network_enabled = True
        controller.weather.worker = BusyWorker()
        controller.weather.refresh()
        self.assertEqual(main.requests, [(FMI_RADAR_URL, True, True)])
        self.assertEqual(desktop.requests, [(FMI_RADAR_URL, True, True)])
        main.requests.clear(); desktop.requests.clear()
        controller.open_page('overview'); self.app.processEvents()
        controller.weather.refresh()
        self.assertEqual(main.requests, [])
        self.assertEqual(desktop.requests, [(FMI_RADAR_URL, True, True)])

    def test_failed_mode_save_restores_selector_without_navigating(self):
        controller, page = self.start()
        before = copy.deepcopy(controller.state.data)
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')), \
             patch.object(controller, 'storage_error') as error:
            self.choose(page.view, 'map')
        error.assert_called_once()
        self.assertEqual(controller.state.data, before)
        self.assertEqual(page.view.currentData(), 'graph')
        self.assertIsNone(page.weather_web)

    def test_failed_provider_save_retains_live_provider_forecast_and_views(self):
        controller, page = self.start()
        self.choose(page.view, 'map')
        before = copy.deepcopy(controller.state.data)
        saved = controller.state.path.read_bytes()
        main, desktop = page.weather_web, controller.weather.web_view
        main.requests.clear(); desktop.requests.clear()
        forecast, cache = controller.weather.forecast, controller.weather.cache
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')), \
             patch.object(controller, 'storage_error') as error:
            self.choose(page.provider, 'windy')
        error.assert_called_once()
        self.assertEqual(controller.state.data, before)
        self.assertEqual(controller.state.path.read_bytes(), saved)
        self.assertEqual(controller.weather.selected, 'foreca')
        self.assertEqual(page.provider.currentData(), 'foreca')
        self.assertIs(controller.weather.forecast, forecast)
        self.assertIs(controller.weather.cache, cache)
        self.assertIs(page.stack.currentWidget(), main)
        self.assertIs(controller.weather.web_view, desktop)
        self.assertEqual(main.requests, [])
        self.assertEqual(desktop.requests, [])
        self.assertIsNone(page.windy)
        self.assertIsNone(controller.weather.windy)

    def test_desktop_context_provider_callback_handles_failed_save(self):
        controller, page = self.start()
        self.choose(page.view, 'map')
        before = copy.deepcopy(controller.state.data)
        main, desktop = page.weather_web, controller.weather.web_view
        main.requests.clear(); desktop.requests.clear()
        menu = controller.weather.make_menu()
        action = next(item for item in menu.actions() if item.text() == 'Vaihda sääpalvelua')
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')), \
             patch.object(controller, 'storage_error') as error:
            action.trigger(); self.app.processEvents()
        error.assert_called_once()
        self.assertEqual(controller.state.data, before)
        self.assertEqual(controller.weather.selected, 'foreca')
        self.assertEqual(page.provider.currentData(), 'foreca')
        self.assertIs(page.stack.currentWidget(), main)
        self.assertIs(controller.weather.web_view, desktop)
        self.assertEqual(main.requests, [])
        self.assertEqual(desktop.requests, [])
        menu.deleteLater()

    def test_shutdown_stops_both_retained_main_and_desktop_web_surfaces(self):
        controller, page = self.start()
        self.choose(page.provider, 'windy')
        main_windy, desktop_windy = page.windy, controller.weather.windy
        self.choose(page.provider, 'fmi'); self.choose(page.view, 'map')
        main_radar, desktop_radar = page.weather_web, controller.weather.web_view
        self.dispose(controller)
        for view in (main_windy, desktop_windy, main_radar, desktop_radar):
            self.assertTrue(view.stopped)


if __name__ == '__main__':
    unittest.main()
