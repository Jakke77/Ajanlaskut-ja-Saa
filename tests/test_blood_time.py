"""Veri Aika's agreed civil-clock rules, including Finnish DST transitions."""
from datetime import date, datetime, timedelta, timezone
import unittest
from zoneinfo import ZoneInfo

from asaa import blood_time as blood


class BloodTimeTests(unittest.TestCase):
    def test_epoch_is_exactly_the_first_day_of_the_first_week(self):
        self.assertEqual(blood.EPOCH.isoformat(), '2026-06-26T01:07:07+03:00')
        item = blood.at(blood.EPOCH)
        self.assertEqual((item.ordinal, item.week, item.weekday), (0, 1, 0))
        self.assertEqual(item.label, '1. päivä · 1. viikko')
        self.assertEqual(item.system, 'blood')

    def test_one_microsecond_before_epoch_is_explicitly_before_start(self):
        item = blood.at(blood.EPOCH - timedelta(microseconds=1))
        self.assertEqual(item.ordinal, -1)
        self.assertEqual(item.civil, date(2026, 6, 25))
        self.assertIn('ennen Veri Ajan alkua', item.label)

    def test_week_changes_only_at_seventh_local_day_cutover(self):
        boundary = blood.boundary(date(2026, 7, 3))
        before = blood.at(boundary - timedelta(microseconds=1))
        after = blood.at(boundary)
        self.assertEqual((before.week, before.weekday), (1, 6))
        self.assertEqual((after.week, after.weekday), (2, 0))
        self.assertEqual(blood.next_week(blood.EPOCH), boundary)
        self.assertEqual(blood.next_week(boundary), blood.boundary(date(2026, 7, 10)))

    def test_midnight_does_not_change_veri_day(self):
        midnight = datetime(2026, 7, 3, tzinfo=blood.ZONE)
        self.assertEqual(blood.at(midnight).civil, date(2026, 7, 2))
        self.assertEqual(blood.at(midnight).weekday, 6)

    def test_week_count_does_not_restart_at_year_or_anniversary(self):
        for day in (date(2027, 1, 1), date(2027, 6, 26), date(2028, 2, 29)):
            item = blood.from_date(day)
            self.assertEqual(item.ordinal, (day - date(2026, 6, 26)).days)
            self.assertEqual(item.week, item.ordinal // 7 + 1)
        self.assertEqual(blood.from_date(date(2027, 6, 26)).week, 53)

    def test_week_duration_changes_across_dst_but_wall_time_stays_fixed(self):
        for day, hours in ((date(2027, 3, 26), 167), (date(2026, 10, 23), 169)):
            with self.subTest(day=day):
                start = blood.boundary(day)
                end = blood.next_week(start)
                self.assertEqual(blood.at(start).weekday, 0)
                self.assertEqual((end.hour, end.minute, end.second), (1, 7, 7))
                self.assertEqual(end.timestamp() - start.timestamp(), hours * 3600)
                self.assertEqual(blood.at(end).week, blood.at(start).week + 1)

    def test_dst_days_have_23_or_25_hours_but_one_calendar_day(self):
        for day, hours in ((date(2027, 3, 28), 23), (date(2026, 10, 25), 25)):
            with self.subTest(day=day):
                start = blood.boundary(day)
                end = blood.boundary(day + timedelta(days=1))
                self.assertEqual(end.timestamp() - start.timestamp(), hours * 3600)
                self.assertEqual(blood.at(end).ordinal - blood.at(start).ordinal, 1)

    def test_same_instant_is_identical_in_all_input_timezones(self):
        for zone in (timezone.utc, ZoneInfo('America/New_York'), ZoneInfo('Asia/Tokyo')):
            self.assertEqual(blood.at(blood.EPOCH.astimezone(zone)), blood.at(blood.EPOCH))
            self.assertEqual(blood.next_week(blood.EPOCH.astimezone(zone)), blood.next_week(blood.EPOCH))

    def test_date_selection_means_its_boundary_not_midnight(self):
        selected = date(2026, 6, 26)
        self.assertEqual(blood.from_date(selected), blood.at(blood.boundary(selected)))
        self.assertEqual(blood.from_date(selected).day_name, '1. päivä')

    def test_naive_datetimes_and_wrong_input_types_are_not_inferred(self):
        for function in (blood.at, blood.next_week):
            with self.assertRaises(ValueError):
                function(datetime(2026, 6, 26, 1, 7, 7))
        with self.assertRaises(TypeError):
            blood.at(date(2026, 6, 26))
        with self.assertRaises(TypeError):
            blood.boundary(blood.EPOCH)


if __name__ == '__main__':
    unittest.main()
