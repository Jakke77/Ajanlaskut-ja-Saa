"""Real star catalogue, an independent ERFA reference, and sky orientation."""
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

from asaa.otava import STARS, LINKS, sky_at

UTC = timezone.utc


class OtavaTests(unittest.TestCase):
    def test_exactly_seven_catalogue_stars_and_connected_dipper(self):
        self.assertEqual(tuple(s.name for s in STARS),
                         ('Dubhe', 'Merak', 'Phecda', 'Megrez', 'Alioth', 'Mizar', 'Alkaid'))
        self.assertEqual(len(LINKS), 7)  # bowl closed, three-segment handle
        self.assertEqual({i for edge in LINKS for i in edge}, set(range(7)))
        self.assertNotIn('Alcor', [s.name for s in STARS])

    def test_all_seven_stay_above_oulu_horizon_and_inside_fixed_field(self):
        for hour in range(24):
            stars = sky_at(datetime(2026, 10, 24, hour, tzinfo=UTC))
            self.assertEqual(len(stars), 7)
            for star in stars:
                with self.subTest(hour=hour, star=star.name):
                    self.assertGreater(star.altitude, 24)
                    self.assertLessEqual(star.altitude, 90)
                    self.assertGreaterEqual(star.azimuth, 0)
                    self.assertLess(star.azimuth, 360)
                    self.assertLess(math.hypot(star.x, star.y), 1)

    def test_same_instant_has_identical_geometry_in_every_input_zone(self):
        instant = datetime(2026, 10, 24, 12, tzinfo=UTC)
        expected = sky_at(instant)
        for zone in ('Europe/Helsinki', 'Asia/Tokyo', 'America/New_York'):
            self.assertEqual(sky_at(instant.astimezone(ZoneInfo(zone))), expected)

    def test_six_hours_rotate_constellation_without_resizing(self):
        first = sky_at(datetime(2026, 10, 24, 3, tzinfo=UTC))
        later = sky_at(datetime(2026, 10, 24, 9, tzinfo=UTC))
        for a, b in zip(first, later):
            self.assertAlmostEqual(math.hypot(a.x, a.y), math.hypot(b.x, b.y), places=10)
            delta = ((math.atan2(b.y, b.x) - math.atan2(a.y, a.x) + math.pi)
                     % (2 * math.pi) - math.pi)
            # Looking north: upper culmination moves toward the left/west.
            self.assertAlmostEqual(math.degrees(delta), -90.2464, delta=.002)

    def test_geometric_positions_match_independent_astropy_erfa_references(self):
        # Astropy is used only to prepare the versioned reference fixture;
        # the application and this offline test need no Astropy dependency.
        reference = json.loads((Path(__file__).parent / 'fixtures' /
                                'otava-astropy.json').read_text(encoding='utf-8'))
        for frame in reference['fixtures']:
            moment = datetime.fromisoformat(frame['utc'])
            for actual, expected in zip(sky_at(moment), frame['stars']):
                with self.subTest(moment=moment, star=actual.name):
                    self.assertEqual(actual.name, expected['name'])
                    a, b = map(math.radians, (actual.altitude, expected['altitude']))
                    delta = math.radians(actual.azimuth - expected['azimuth'])
                    cosine = math.sin(a)*math.sin(b) + math.cos(a)*math.cos(b)*math.cos(delta)
                    separation = math.degrees(math.acos(max(-1, min(1, cosine))))
                    self.assertLess(separation, .01)  # 0.6 arcminutes on the sky

    def test_sidereal_day_repeats_but_solar_day_does_not(self):
        instant = datetime(2026, 10, 24, 12, tzinfo=UTC)
        first = sky_at(instant)
        sidereal = sky_at(instant + timedelta(seconds=86164.0905))
        solar = sky_at(instant + timedelta(days=1))
        for a, b, c in zip(first, sidereal, solar):
            self.assertLess(math.hypot(a.x-b.x, a.y-b.y), .00001)
            self.assertGreater(math.hypot(a.x-c.x, a.y-c.y), .008)

    def test_both_edges_of_supported_date_range_are_finite(self):
        for year in (1900, 2100):
            for item in sky_at(datetime(year, 1, 1, tzinfo=UTC)):
                self.assertTrue(all(math.isfinite(value) for value in
                                    (item.x, item.y, item.altitude, item.azimuth)))

    def test_naive_and_out_of_range_instants_are_rejected(self):
        for instant in (datetime(2026, 10, 24), datetime(1800, 1, 1, tzinfo=UTC),
                        datetime(2101, 1, 1, tzinfo=UTC)):
            with self.assertRaises(ValueError):
                sky_at(instant)


if __name__ == '__main__':
    unittest.main()
