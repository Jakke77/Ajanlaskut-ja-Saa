"""Stable original names, complete cycles and pre-epoch birthday lookup."""
from datetime import date, timedelta
import unittest

from asaa.namedays import catalog, names_at, names_for_day, cycle_position
from asaa.calendar import Calendars
from asaa import finnish_calendar as folk


class NamedayTests(unittest.TestCase):
    def test_complete_unique_name_pairs_for_every_day(self):
        for system,count in [('shadow',390),('star',510),('finnish',390)]:
            pairs=catalog()[system]
            self.assertEqual(len(pairs),count)
            self.assertEqual(len({p.male for p in pairs}),count)
            self.assertEqual(len({p.female for p in pairs}),count)
            self.assertTrue(all(p.male and p.female and p.male!=p.female for p in pairs))

    def test_names_remain_fixed_and_repeat_only_after_whole_calendar_year(self):
        day=date(2026,10,23)
        for system,length in [('shadow',390),('star',510)]:
            self.assertEqual(names_for_day(system,day),names_for_day(system,day+timedelta(days=length)))
            self.assertNotEqual(names_for_day(system,day),names_for_day(system,day+timedelta(days=1)))
            self.assertEqual(Calendars().convert(system,day).names,names_for_day(system,day))
        self.assertEqual(names_at('shadow',0,0).male,'Varjomieli')
        self.assertEqual(names_at('star',0,0).female,'Valotar')

    def test_birthday_before_epoch_projects_back_without_changing_date_conversion(self):
        birthday=date(1985,2,14)
        for system in ['shadow','star']:
            month,day=cycle_position(system,birthday)
            self.assertEqual(names_for_day(system,birthday),names_at(system,month,day))
            with self.assertRaises(ValueError):Calendars().convert(system,birthday)

    def test_name_cycle_uses_configured_star_epoch(self):
        day=date(2026,10,23)
        self.assertNotEqual(names_for_day('star',day,date(2026,7,1)),names_for_day('star',day,date(2025,7,1)))

    def test_invalid_name_positions_are_not_silently_wrapped(self):
        for args in [('unknown',0,0),('star',17,0),('shadow',13,0),('shadow',0,30),('star',False,0)]:
            with self.assertRaises(ValueError):names_at(*args)


class FinnishCalendarTests(unittest.TestCase):
    def test_contemporary_date_uses_actual_october2026_new_moon(self):
        day=folk.convert(date(2026,10,23))
        self.assertEqual((day.period.month,day.day),(10,14))
        self.assertEqual(day.period.start,date(2026,10,10))
        self.assertEqual(day.period.length,30)

    def test_vaahtokuu_only_in_13_lunation_year_after_february(self):
        leap=folk.year_months(2027);ordinary=folk.year_months(2025)
        self.assertEqual(len(leap),13);self.assertEqual(len(ordinary),12)
        foam=next(i for i,item in enumerate(leap) if item.month==2)
        self.assertEqual((leap[foam-1].month,leap[foam+1].month),(1,3))
        self.assertFalse(any(item.month==2 for item in ordinary))
        self.assertEqual(folk.convert(date(2028,2,25)).period.month,2)

    def test_all_months_29_or30_days_no_gaps_and_boundary_namedays(self):
        for year in range(2024,2043):
            periods=folk.year_months(year)
            self.assertIn(len(periods),(12,13))
            for a,b in zip(periods,periods[1:]):self.assertEqual(a.end,b.start)
            for item in periods:
                self.assertIn(item.length,(29,30))
                first=folk.convert(item.start);last=folk.convert(item.end-timedelta(days=1))
                self.assertEqual(first.day,1);self.assertEqual(last.day,item.length)
                self.assertTrue(first.names.male);self.assertTrue(last.names.female)
            self.assertEqual(periods[-1].end,folk.year_months(year+1)[0].start)

    def test_december_contains_winter_solstice_and_range_is_explicit(self):
        for year in range(2024,2033):
            december=folk.convert(date(year,12,21))
            # Solstice can fall on 22 December; use the precise instant.
            instant=folk._from_tt(folk.Sun.get_equinox_solstice(year,target='winter')).astimezone(folk.ZONE)
            self.assertEqual(folk.convert(instant.date()).period.month,12)
        with self.assertRaises(ValueError):folk.convert(date(1800,1,1))

    def test_phase_seed_does_not_skip_december2023_new_moon(self):
        # Independent USNO phase date: 2023-12-12 23:32 UTC = 13 December Helsinki.
        start=folk._from_tt(folk._winter_new_moon(2023)).astimezone(folk.ZONE)
        self.assertEqual(start.date(),date(2023,12,13))

    def test_declared_year_range_never_skips_a_lunation_before_solstice(self):
        for year in range(1899,2102):
            first=folk._winter_new_moon(year)
            solstice=folk.Sun.get_equinox_solstice(year,target='winter')
            self.assertGreaterEqual(float(solstice)-float(first),0,year)
            self.assertLess(float(solstice)-float(first),30,year)
            self.assertIn(len(folk.year_months(year)),(12,13),year)


if __name__=='__main__':unittest.main()
