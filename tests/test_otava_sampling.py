"""One real Oulu sky sample shared by all displays every 26 elapsed minutes."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from asaa import otava


class SkySamplingTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 10, 25, 0, 55, tzinfo=timezone.utc)

    def test_first_sample_is_immediate_and_refresh_is_exactly_26_minutes(self):
        sampler = otava.SkySampler()
        with patch.object(otava, 'sky_at', wraps=otava.sky_at) as calculate:
            first = sampler.sample(self.start)
            self.assertEqual(first.moment, self.start)
            self.assertIs(sampler.sample(self.start + timedelta(minutes=26, microseconds=-1)), first)
            second = sampler.sample(self.start + timedelta(minutes=26))
            self.assertIsNot(second, first)
            self.assertEqual(calculate.call_count, 2)
        self.assertNotEqual(first.stars, second.stars)
        self.assertEqual(second.stars, otava.sky_at(second.moment))

    def test_sleep_and_clock_correction_refresh_without_replaying_missed_samples(self):
        sampler = otava.SkySampler()
        first = sampler.sample(self.start)
        awake = sampler.sample(self.start + timedelta(hours=9))
        self.assertEqual(awake.moment, self.start + timedelta(hours=9))
        corrected = sampler.sample(self.start)
        self.assertEqual(corrected.stars, first.stars)

    def test_helsinki_winter_time_fold_uses_elapsed_utc_minutes(self):
        sampler = otava.SkySampler()
        zone = ZoneInfo('Europe/Helsinki')
        first = sampler.sample(self.start.astimezone(zone))
        self.assertIs(sampler.sample((self.start + timedelta(minutes=25)).astimezone(zone)), first)
        updated = sampler.sample((self.start + timedelta(minutes=26)).astimezone(zone))
        self.assertEqual(updated.moment, self.start + timedelta(minutes=26))

    def test_views_share_one_controller_sample_and_named_tail_direction(self):
        controller = SimpleNamespace()
        first = otava.sampled_sky(controller, self.start)
        self.assertIs(otava.sampled_sky(controller, self.start + timedelta(seconds=1)), first)
        other = SimpleNamespace()
        self.assertIsNot(otava.sampled_sky(other, self.start), first)
        tail = next(s for s in first.stars if s.name == 'Alkaid')
        description = otava.tail_description(first.stars)
        self.assertIn('Alkaid', description)
        self.assertIn(f'{tail.azimuth:.1f}°', description)
        self.assertIn(f'{tail.altitude:.1f}°', description)

    def test_invalid_time_is_rejected_even_after_a_valid_sample(self):
        sampler = otava.SkySampler()
        first = sampler.sample(self.start)
        for invalid in (datetime(2026, 10, 25), datetime(1800, 1, 1, tzinfo=timezone.utc)):
            with self.assertRaises(ValueError):
                sampler.sample(invalid)
        self.assertIs(sampler.snapshot, first)


class SkySamplingUiTests(unittest.TestCase):
    def test_dashboard_calendar_and_widget_share_geometry_and_last_checked_time(self):
        from tests.test_veri_integration import VeriIntegrationTests
        from asaa.otava_ui import OtavaView
        case = VeriIntegrationTests('test_menu_calendar_selector_and_overview_use_actual_cutover')
        case.setUpClass()
        case.setUp()
        try:
            case.now = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
            case.controller._otava_sampler = otava.SkySampler()
            case.controller.clock_changed.emit()
            dashboard = case.controller.window.page_widgets['overview'].otava
            calendar = case.controller.window.page_widgets['blood'].sky
            self.assertIs(dashboard.snapshot, calendar.snapshot)
            first = dashboard.snapshot
            case.controller.set_widget('blood', True)
            widget = case.controller.widgets['blood']
            widget.grab()
            self.assertIn('Alkaid', widget.toolTip())
            self.assertIn('26 min', widget.toolTip())
            case.now += timedelta(minutes=25)
            case.controller.clock_changed.emit()
            self.assertIs(dashboard.snapshot, first)
            case.now += timedelta(minutes=1)
            case.controller.clock_changed.emit()
            self.assertIsNot(dashboard.snapshot, first)
            self.assertIs(dashboard.snapshot, calendar.snapshot)
            self.assertIn('Ympyröity', dashboard.toolTip())
            self.assertFalse(dashboard.grab().isNull())
        finally:
            case.tearDown()


if __name__ == '__main__':
    unittest.main()
