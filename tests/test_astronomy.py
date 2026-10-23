"""Independent USNO reference events, real phases and civil-time edge cases."""
from datetime import date, datetime, timedelta, timezone
import unittest
from zoneinfo import ZoneInfo

from asaa.astronomy import (moon_at, moon_on, solar_day, lunar_day, phase_events,
                            event_label, duration_label)
from asaa.calendar import Calendars

UTC = timezone.utc


class AstronomyTests(unittest.TestCase):
    # US Naval Observatory APIs, retrieved 2026-10-23 with TLS verification:
    # /api/moon/phases/year?year=2026
    # /api/rstt/oneday?date=2026-10-23&coords=65.0701,25.5071&tz=3
    # /api/rstt/oneday?date=2026-03-08&coords=40.7128,-74.0060&tz=-4
    def test_october_principal_phases_match_usno_within_two_minutes(self):
        actual = {name:instant for instant,name in phase_events(date(2026,10,19))
                  if instant.year==2026 and instant.month==10}
        references = [('Uusikuu',10,15,50),('Ensimmäinen neljännes',18,16,12),
                      ('Täysikuu',26,4,12)]
        for name,day,hour,minute in references:
            with self.subTest(name=name):
                reference=datetime(2026,10,day,hour,minute,tzinfo=UTC)
                self.assertLess(abs((actual[name]-reference).total_seconds()),120)
                self.assertEqual(moon_at(reference).name,name)
        full=actual['Täysikuu'].astimezone(ZoneInfo('Europe/Helsinki'))
        self.assertEqual(full.hour,6)  # Finland's winter time starts on 25 October.

    def test_reported_october19_bug_is_growing_more_than_half_in_both_calendars(self):
        day=date(2026,10,19);calendars=Calendars()
        labels=[calendars.convert(key,day).phase for key in ('shadow','star','civil')]
        self.assertEqual(len(set(labels)),1)
        self.assertIn('Kasvava kuu',labels[0])
        info=moon_on(day)
        self.assertGreater(info.illumination,.5);self.assertLess(info.illumination,.7)
        self.assertNotIn('Täysikuu',labels[0]);self.assertNotIn('Vähenevä',labels[0])

    def test_real_crescent_and_waning_crescent_have_different_sides(self):
        waxing=moon_on(date(2026,10,13));waning=moon_on(date(2026,10,7))
        self.assertEqual(waxing.name,'Kasvava sirppi')
        self.assertEqual(waning.name,'Vähenevä sirppi')
        self.assertLess(waxing.angle,90);self.assertGreater(waning.angle,270)
        self.assertLess(waxing.illumination,.5);self.assertLess(waning.illumination,.5)

    def test_oulu_rise_set_and_civil_twilight_match_usno(self):
        sun=solar_day(date(2026,10,23),65.0701,25.5071,'Europe/Helsinki')
        moon=lunar_day(date(2026,10,23),65.0701,25.5071,'Europe/Helsinki')
        for events,clock in [(sun.sun.rises,'08:36'),(sun.sun.sets,'17:27'),
                             (sun.civil.rises,'07:44'),(sun.civil.sets,'18:19'),
                             (moon.rises,'16:47'),(moon.sets,'04:09')]:
            with self.subTest(clock=clock):self.assertEqual(event_label(events,'missing'),clock)
        self.assertAlmostEqual(sun.sun.duration/3600,8+50/60,delta=2/60)

    def test_new_york_dst_day_and_missing_moonrise_are_not_polar_night(self):
        day=date(2026,3,8);args=(day,40.7128,-74.006,'America/New_York')
        sun=solar_day(*args);moon=lunar_day(*args)
        self.assertEqual((sun.end-sun.start).total_seconds(),23*3600)
        self.assertEqual(event_label(sun.sun.rises,'missing'),'07:19')
        self.assertEqual(event_label(sun.sun.sets,'missing'),'18:55')
        self.assertEqual(moon.rises,())
        self.assertEqual(event_label(moon.sets,'missing'),'09:23')
        self.assertEqual(moon.state,'crosses')

    def test_finnish_dst_dates_have_23_and_25_real_hours(self):
        for day,hours in [(date(2026,3,29),23),(date(2026,10,25),25)]:
            result=solar_day(day,65.0701,25.5071,'Europe/Helsinki')
            self.assertEqual((result.end-result.start).total_seconds(),hours*3600)
            for event in result.sun.rises+result.sun.sets:self.assertEqual(event.date(),day)
            segment=result.sun.segments[0]
            self.assertAlmostEqual(result.sun.duration,segment[1].timestamp()-segment[0].timestamp(),places=2)

    def test_polar_day_and_night_preserve_twilight(self):
        args=(69.6492,18.9553,'Europe/Oslo')
        summer=solar_day(date(2026,6,21),*args);winter=solar_day(date(2026,12,21),*args)
        self.assertEqual(summer.sun.state,'always_above')
        self.assertEqual(duration_label(summer.sun.duration),'24 h 00 min')
        self.assertEqual(winter.sun.state,'always_below')
        self.assertEqual(winter.sun.duration,0)
        self.assertTrue(winter.civil.rises);self.assertTrue(winter.civil.sets)

    def test_same_instant_has_same_moon_independently_of_zone(self):
        instant=datetime(2026,10,23,12,tzinfo=UTC)
        self.assertEqual(moon_at(instant),moon_at(instant.astimezone(ZoneInfo('Pacific/Auckland'))))
        with self.assertRaises(ValueError):moon_at(instant.replace(tzinfo=None))

    def test_moon_age_and_next_phases_do_not_skip_the_previous_lunation(self):
        for offset in range(0,366,5):
            day=date(2026,1,1)+timedelta(days=offset)
            self.assertGreaterEqual(moon_on(day).age,0)
            self.assertLess(moon_on(day).age,30,day)
        # USNO: Last Quarter 2026-10-03 13:25 UTC must remain in nearby events.
        events=[instant for instant,name in phase_events(date(2026,10,19))
                if name=='Viimeinen neljännes' and instant.date()==date(2026,10,3)]
        self.assertEqual(len(events),1)
        self.assertLess(abs((events[0]-datetime(2026,10,3,13,25,tzinfo=UTC)).total_seconds()),120)

    def test_unsupported_dates_and_coordinates_are_explicit(self):
        for day in [date(1,1,1),date(2101,1,1),date(9999,12,31)]:
            with self.assertRaises(ValueError):moon_on(day)
        for lat,lon in [(91,0),(0,181),(float('nan'),0)]:
            with self.assertRaises(ValueError):solar_day(date(2026,10,23),lat,lon,'UTC')


if __name__=='__main__':unittest.main()
