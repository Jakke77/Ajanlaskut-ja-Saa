"""Shared official weather pages inherit the tested lazy browser lifecycle."""
import os
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent, QUrl, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from asaa.weather import windy_view
from asaa.weather.providers import Place
from asaa.weather.web_sources import FMI_RADAR_URL, foreca_map_url, forecast_url
from tests.test_windy_view import FakePage, FakeProfile, FakeView


class FakeForecastView(FakeView):
    _zoom = 1.0

    def setZoomFactor(self, zoom):
        self._zoom = zoom

    def zoomFactor(self):
        return self._zoom


class WeatherWebViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.patches = [
            patch.object(windy_view, 'QWebEngineView', FakeForecastView),
            patch.object(windy_view, 'QWebEngineProfile', FakeProfile),
            patch.object(windy_view, 'QWebEnginePage', FakePage),
        ]
        for replacement in self.patches:
            replacement.start()
        self.widgets = []
        self.parents = []
        self.place = Place('Oulu', 65.0701, 25.5071)
        self.widget = self.create()
        self.web = self.widget.view

    def create(self, **kwargs):
        widget = windy_view.WeatherWebView(**kwargs)
        widget.resize(640, 480)
        self.widgets.append(widget)
        return widget

    def tearDown(self):
        for widget in self.widgets:
            widget.stop()
            widget.hide()
            widget.deleteLater()
        for parent in self.parents:
            parent.hide()
            parent.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        for replacement in reversed(self.patches):
            replacement.stop()

    def events(self):
        self.app.processEvents()

    def test_hidden_provider_changes_request_only_latest_map_when_shown(self):
        self.widget.load_source('foreca', 'map', self.place,
                                foreca_url='https://www.foreca.fi/Finland/Oulu')
        self.widget.load_source('fmi', 'map', self.place)
        self.events()
        self.assertEqual(self.web.requests, [])
        self.widget.show()
        self.events()
        self.assertEqual(self.web.requests, [FMI_RADAR_URL])
        self.assertEqual(self.web.accessibleName(), 'Ilmatieteen laitoksen sadekartta')
        self.assertEqual(self.widget.browser_button.text(), 'Avaa Ilmatieteen laitos selaimessa')

    def test_foreca_cached_city_source_does_not_repeat_coordinate_map(self):
        self.widget.show()
        self.widget.load_source('foreca', 'map', self.place)
        self.events()
        self.widget.load_source('foreca', 'map', self.place,
                                foreca_url='https://www.foreca.fi/Finland/Oulu')
        self.events()
        self.assertEqual(self.web.requests, [foreca_map_url(place=self.place)])
        self.web.loadFinished.emit(True)
        self.events()
        self.assertEqual(self.web.requests,
                         [foreca_map_url(place=self.place)])

    def test_windy_graph_uses_own_forecast_and_same_profile_across_modes(self):
        self.widget.load_source('fmi', 'map', self.place)
        self.widget.show()
        self.events()
        profile = self.widget.profile
        self.web.loadFinished.emit(True)
        self.widget.load_source('windy', 'graph', self.place)
        self.events()
        self.assertEqual(self.web.requests, [FMI_RADAR_URL, forecast_url(self.place)])
        self.assertEqual(self.web.accessibleName(), 'Windyn tuntiennuste')
        self.assertIn('Windyn tuntiennustetta', self.widget.status.text())
        self.assertIs(self.widget.profile, profile)
        self.web.loadFinished.emit(True)
        self.widget.load_source('windy', 'graph', self.place, force=True)
        self.events()
        self.assertEqual(self.web.requests[-2:], [forecast_url(self.place)] * 2)

    def test_forecast_uses_official_short_viewport_and_map_restores_full_height(self):
        self.widget.resize(900, 700)
        self.widget.show()
        self.widget.load_source('windy', 'graph', self.place)
        self.events()
        self.assertEqual(self.web.maximumHeight(), 187)
        self.assertEqual(self.web.minimumHeight(), 187)
        self.assertEqual(self.web.height(), 187)
        self.assertEqual(self.widget.layout().alignment(), Qt.AlignmentFlag.AlignTop)
        self.assertTrue(self.widget.browser_button.isVisible())
        self.web.loadFinished.emit(True)
        self.widget.load_source('fmi', 'map', self.place)
        self.events()
        self.assertEqual(self.web.maximumHeight(), 16777215)
        self.assertEqual(self.web.minimumHeight(), 0)
        self.assertGreater(self.web.height(), 500)
        self.assertEqual(self.widget.layout().alignment(), Qt.AlignmentFlag(0))
        self.assertEqual(self.web.requests, [forecast_url(self.place), FMI_RADAR_URL])

    def test_small_forecast_frame_keeps_every_row_above_browser_and_error_controls(self):
        parent = QWidget()
        self.parents.append(parent)
        parent.resize(432, 276)
        self.widget.setParent(parent)
        self.widget.setGeometry(22, 55, 389, 189)
        parent.show()
        self.widget.show()
        self.widget.load_source('windy', 'graph', self.place)
        self.events()
        self.web.loadFinished.emit(True)
        self.events()
        self.assertEqual(self.widget.height(), 189)
        self.assertLess(self.web.height(), 187)
        self.assertAlmostEqual(self.web.height() / self.web.zoomFactor(), 187)
        self.assertGreater(self.widget.browser_button.y(), self.web.geometry().bottom())
        self.assertLessEqual(self.widget.browser_button.geometry().bottom(), 188)
        self.widget.resize(900, 700)
        self.events()
        self.assertEqual(self.web.height(), 187)
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.widget.resize(389, 189)
        self.widget.load_source('windy', 'graph', self.place, force=True)
        self.events()
        self.web.loadFinished.emit(False)
        self.events()
        self.assertAlmostEqual(self.web.height() / self.web.zoomFactor(), 187)
        self.assertGreater(self.widget.status.y(), self.web.geometry().bottom())
        self.assertGreater(self.widget.browser_button.y(), self.widget.retry_button.geometry().bottom())
        self.assertLessEqual(self.widget.browser_button.geometry().bottom(), 188)
        self.widget.load_source('fmi', 'map', self.place)
        self.events()
        self.assertEqual(self.web.zoomFactor(), 1.0)
        self.assertEqual(self.web.minimumHeight(), 0)

    def test_failed_foreca_map_has_honest_labels_and_explicit_retry(self):
        self.widget.load_source('foreca', 'map', self.place)
        self.widget.show()
        self.events()
        self.web.loadFinished.emit(False)
        error = self.widget.status.text()
        self.assertIn('Forecan sadekartta ei latautunut', error)
        self.widget.load_source('foreca', 'map', self.place)
        self.events()
        self.assertEqual(len(self.web.requests), 1)
        self.assertEqual(self.widget.status.text(), error)
        self.widget.retry_button.click()
        self.events()
        self.assertEqual(len(self.web.requests), 2)

    def test_source_switch_during_load_does_not_misattribute_completed_error(self):
        self.widget.load_source('foreca', 'map', self.place)
        self.widget.show()
        self.events()
        self.widget.load_source('windy', 'graph', self.place)
        self.web.loadFinished.emit(False)
        self.assertIn('Forecan sadekartta ei latautunut', self.widget.status.text())
        self.events()
        self.assertIn('Windyn tuntiennustetta', self.widget.status.text())
        self.web.loadFinished.emit(False)
        self.assertIn('Windyn tuntiennuste ei latautunut', self.widget.status.text())

    def test_browser_fallback_uses_validated_foreca_destination(self):
        with patch.object(windy_view, 'QWebEngineView', None):
            fallback = self.create()
        fallback.load_source('foreca', 'map', self.place,
                             foreca_url='https://evil.test/Finland/Oulu')
        fallback.show()
        self.events()
        self.assertIn('Forecan sadekartta tarvitsee Qt WebEngine',
                      '\n'.join(label.text() for label in fallback.findChildren(QLabel)))
        with patch.object(windy_view.QDesktopServices, 'openUrl') as open_url:
            open_url.assert_not_called()
            fallback.browser_button.click()
            self.assertEqual(open_url.call_args.args[0].toString(QUrl.ComponentFormattingOption.FullyEncoded),
                             foreca_map_url(place=self.place))

    def test_native_graphs_are_rejected_without_mutating_selected_source(self):
        self.widget.load_source('windy', 'graph', self.place)
        original = self.widget.url
        for provider in ('yr', 'foreca', 'fmi', 'unknown'):
            with self.subTest(provider=provider), self.assertRaises(ValueError):
                self.widget.load_source(provider, 'graph', self.place)
        self.assertEqual(self.widget.url, original)
        self.assertEqual(self.web.requests, [])

    def test_network_disabled_forecast_has_correct_labels_without_webengine(self):
        offline = self.create(network=False)
        offline.load_source('windy', 'graph', self.place)
        offline.show()
        self.events()
        self.assertIsNone(offline.view)
        self.assertIn('Windy · tuntiennuste (verkkohaku pois',
                      '\n'.join(label.text() for label in offline.findChildren(QLabel)))
        self.assertTrue(offline.browser_button.isEnabled())

    def test_stopped_shared_browser_ignores_future_source_loads(self):
        self.widget.load_source('windy', 'graph', self.place)
        self.widget.show()
        self.widget.stop()
        self.widget.load_source('fmi', 'map', self.place, force=True)
        self.events()
        self.assertEqual(self.web.requests, [])
        self.assertIsNone(self.widget.view)


if __name__ == '__main__':
    unittest.main()
