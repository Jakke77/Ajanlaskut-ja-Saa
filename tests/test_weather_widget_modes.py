"""Saved desktop weather modes and refresh routing without external requests."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication, QWidget

from asaa.app import Controller
from asaa.state import State
from asaa.weather.providers import Place
from asaa.weather.web_sources import source_url
from tests.test_icon_ui import MemoryIcons
from tests.test_wallpapers import MemoryBackend
from tests.test_windy_startup import FakeWindy, BusyWorker


class FakeWeatherWeb(QWidget):
    def __init__(self, parent=None, *, network=True):
        super().__init__(parent)
        self.url = ''
        self.requests = []
        self.stopped = False

    def load_source(self, provider, mode, place, zoom=9, layer='temp', foreca_url='', *, force=False):
        url = source_url(provider, mode, place, zoom, layer, foreca_url)
        if url != self.url or force:
            self.url = url
            self.requests.append((provider, mode, url, force))

    def stop(self):
        self.stopped = True


class WeatherWidgetModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='asaa-weather-modes-')
        self.root = Path(self.temporary.name)
        self.controllers = []
        self.patches = [
            patch.dict(os.environ, {'XDG_DATA_HOME': str(self.root / 'data')}),
            patch('asaa.weather.widget.WindyView', FakeWindy),
            patch('asaa.weather.widget.WeatherWebView', FakeWeatherWeb),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for controller in reversed(self.controllers):
            controller.weather.worker = None
            controller.shutdown()
            controller.window.hide(); controller.window.deleteLater()
            for widget in controller.widgets.values():
                widget.hide(); widget.deleteLater()
            controller.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    def start(self, *, desktop=True, path=None):
        state = State(path or self.root / 'state.json')
        widgets = {key: False for key in state.settings['widgets']}
        widgets['weather'] = desktop
        state.configure({'widgets': widgets})
        controller = Controller(self.app, state, network=False,
                                wallpaper_backend=MemoryBackend(), icon_backend=MemoryIcons())
        self.controllers.append(controller)
        controller.tick_timer.stop(); controller.weather.timer.stop(); controller.daily.timer.stop()
        controller.restore_widgets()
        self.app.processEvents()
        return controller

    def test_modes_are_saved_per_provider_and_yr_remains_graph_only(self):
        controller = self.start()
        owner = controller.weather
        self.assertEqual(owner.view_mode, 'graph')
        owner.set_view_mode('map')
        self.assertTrue(owner.uses_web_view)
        owner.select_provider('fmi')
        self.assertEqual(owner.view_mode, 'graph')
        self.assertFalse(owner.weather_web.isVisible())
        owner.set_view_mode('map')
        owner.select_provider('windy')
        self.assertEqual(owner.view_mode, 'map')
        owner.set_view_mode('graph')
        self.assertFalse(owner.windy.isVisible())
        self.assertIs(owner.web_view, owner.weather_web)
        owner.select_provider('yr')
        self.assertEqual(owner.available_view_modes, ('graph',))
        with self.assertRaises(ValueError):
            owner.set_view_mode('map')
        saved = State(controller.state.path).settings
        self.assertEqual(saved['weather_views'],
                         {'yr': 'graph', 'foreca': 'map', 'fmi': 'map', 'windy': 'graph'})
        owner.select_provider('foreca')
        self.assertEqual(owner.view_mode, 'map')
        self.assertIs(owner.web_view, owner.weather_web)

    def test_hidden_desktop_does_not_create_a_web_view_until_shown(self):
        controller = self.start(desktop=False)
        owner = controller.weather
        owner.select_provider('fmi')
        owner.set_view_mode('map')
        self.assertIsNone(owner.weather_web)
        owner.show()
        self.app.processEvents()
        self.assertEqual(owner.weather_web.requests,
                         [('fmi', 'map', source_url('fmi', 'map', owner.place), False)])
        owner.hide()
        owner.weather_web.requests.clear()
        owner.network_enabled = True
        owner.worker = BusyWorker()
        owner.refresh()
        self.assertEqual(owner.weather_web.requests, [])

    def test_explicit_web_refresh_is_independent_of_a_busy_forecast_worker(self):
        controller = self.start()
        owner = controller.weather
        emitted = []
        owner.web_reload_requested.connect(lambda: emitted.append(owner.selected))
        owner.set_view_mode('map')
        owner.weather_web.requests.clear()
        owner.network_enabled = True
        owner.worker = BusyWorker()
        owner.refresh()
        self.assertEqual(emitted, ['foreca'])
        self.assertEqual(owner.weather_web.requests,
                         [('foreca', 'map', source_url('foreca', 'map', owner.place), True)])
        owner.weather_web.requests.clear()
        owner.refresh(automatic=True)
        self.assertEqual(owner.weather_web.requests, [])
        self.assertEqual(emitted, ['foreca'])
        owner.network_enabled = False
        owner.refresh()
        self.assertEqual(emitted, ['foreca'])

    def test_windy_graph_uses_exact_place_and_keeps_native_forecasts_separate(self):
        controller = self.start()
        owner = controller.weather
        owner.select_provider('windy')
        owner.set_view_mode('graph')
        original_map = owner.windy
        other = Place('Toinen paikka', 62.1, 26.2)
        owner.set_place(other)
        self.assertEqual(owner.weather_web.url, source_url('windy', 'graph', other))
        self.assertIsNone(owner.forecast)
        self.assertFalse(original_map.isVisible())
        owner.select_provider('foreca')
        self.assertFalse(owner.uses_web_view)
        self.assertFalse(owner.weather_web.isVisible())

    def test_resolved_foreca_city_updates_selected_map_without_an_extra_fetch(self):
        controller = self.start()
        owner = controller.weather
        owner.set_view_mode('map')
        cache = owner.caches['foreca']
        cache.path.parent.mkdir(parents=True, exist_ok=True)
        cache.path.write_text(json.dumps({'provider': 'foreca', 'location': owner.place.key,
                                         'source_url': 'https://www.foreca.fi/Finland/Oulu'}))
        owner.provider_received(owner.place.key, 'foreca', None, 'Offline')
        self.assertEqual(owner.weather_web.url,
                         source_url('foreca', 'map', owner.place, foreca_url=owner.foreca_source_url))
        self.assertIsNone(owner.worker)
        self.assertIn('Sadetutka', owner.accessibleName())

    def test_shutdown_stops_both_desktop_web_surfaces(self):
        controller = self.start()
        owner = controller.weather
        owner.select_provider('windy')
        owner.set_view_mode('graph')
        original_map, graph = owner.windy, owner.weather_web
        controller.shutdown()
        self.assertTrue(original_map.stopped)
        self.assertTrue(graph.stopped)
        requests = list(graph.requests)
        owner.network_enabled = True
        owner.refresh(); owner.load_web_view(force=True)
        self.assertEqual(graph.requests, requests)


if __name__ == '__main__':
    unittest.main()
