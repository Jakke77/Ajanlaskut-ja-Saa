import copy
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from asaa.calendar import Calendars
from asaa.state import State, DEFAULTS, atomic_json


class CalendarTests(unittest.TestCase):
    def setUp(self): self.clock = Calendars()

    def test_confirmed_dates(self):
        shadow = self.clock.convert('shadow', date(2026, 10, 7))
        star = self.clock.convert('star', date(2026, 10, 7))
        self.assertEqual((shadow.year, shadow.month, shadow.day), (1, 0, 9))
        self.assertEqual((star.year, star.month, star.day), (1, 3, 8))

    def test_round_trips(self):
        for system in ('shadow', 'star', 'civil'):
            start = date(2026, 9, 28)
            for n in (0, 29, 30, 389, 390, 509, 510, 511, 36400):
                civil = start + timedelta(days=n)
                day = self.clock.convert(system, civil)
                self.assertEqual(self.clock.civil_date(system, day.year, day.month, day.day), civil)

    def test_cycle_boundaries(self):
        self.assertEqual(self.clock.step_month('star', 1, 16, 1), (2, 0))
        self.assertEqual(self.clock.step_month('shadow', 1, 12, 1), (2, 0))
        self.assertEqual(self.clock.step_month('star', 1, 0, -1), (1, 0))
        self.assertEqual(len(self.clock.month_days('civil', 2028, 1)), 29)
        self.assertEqual(len(self.clock.month_days('shadow', 2, 0)), 30)

    def test_supported_upper_bound(self):
        for system in ('shadow', 'star', 'civil'):
            last = self.clock.last_month(system)
            self.assertEqual(self.clock.step_month(system, *last, 1), last)
            days = self.clock.month_days(system, *last)
            self.assertLessEqual(days[-1].civil, date.max)

    def test_epoch_and_zone(self):
        with self.assertRaises(ValueError): self.clock.convert('shadow', date(2026, 9, 27))
        with self.assertRaises(ValueError): self.clock.convert('star', date(2026, 6, 30))
        with self.assertRaises(ValueError): Calendars(star_epoch='2026-07-02')
        self.assertEqual(str(self.clock.now().tzinfo), 'Europe/Helsinki')


class StateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)/'state.json'
        self.state = State(self.path)
    def tearDown(self): self.directory.cleanup()

    def test_defaults(self):
        self.assertEqual(self.state.settings['theme'], 'copper')
        self.assertEqual(self.state.settings['time_theme'], 'calendar')
        self.assertEqual([k for k, v in self.state.settings['widgets'].items() if v], ['combined', 'weather'])
        self.assertEqual(self.state.settings['refresh_minutes'], 77)
        self.assertEqual(self.state.settings['place']['name'], 'Pöllönkangas, Oulu')
        self.assertEqual(self.state.settings['widget_text_scale'],130)
        self.assertEqual(self.state.settings['widget_clock_scale'],100)

    def test_ubuntu_clock_and_shared_theme_are_independent_and_durable(self):
        self.state.configure({'time_theme': 'ubuntu'})
        loaded = State(self.path)
        self.assertEqual(loaded.settings['time_theme'], 'ubuntu')
        self.assertEqual(loaded.settings['theme'], 'copper')
        loaded.configure({'theme': 'ubuntu', 'time_theme': 'calendar'})
        reloaded = State(self.path)
        self.assertEqual(reloaded.settings['theme'], 'ubuntu')
        self.assertEqual(reloaded.settings['time_theme'], 'calendar')
        reloaded.configure({'time_theme': 'shared'})
        self.assertEqual(State(self.path).settings['time_theme'], 'shared')

    def test_theme_change_preserves_saved_content_and_widget_settings(self):
        day = date(2026, 10, 7)
        self.state.save_note(day, 'Oma merkintä')
        self.state.geometry('combined', (500, 60))
        previous = copy.deepcopy(self.state.data)
        self.state.configure({'theme': 'ubuntu', 'time_theme': 'ubuntu'})
        expected = copy.deepcopy(previous)
        expected['settings'].update({'theme': 'ubuntu', 'time_theme': 'ubuntu'})
        self.assertEqual(State(self.path).data, expected)

    def test_invalid_theme_change_is_atomic(self):
        self.state.configure({'theme': 'ubuntu', 'time_theme': 'ubuntu'})
        previous = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        for changes in ({'theme': 'ubuntuu'}, {'time_theme': 'ubuntuu'},
                        {'time_theme': 'frost'}, {'theme': 'copper', 'time_theme': 'unknown'}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError): self.state.configure(changes)
                self.assertEqual(self.state.data, previous)
                self.assertEqual(self.path.read_bytes(), content)

    def test_old_state_gains_font_controls_without_losing_preferences(self):
        old=copy.deepcopy(self.state.data)
        old['settings'].pop('widget_text_scale');old['settings'].pop('widget_clock_scale')
        old['settings']['scale']=77;old['settings']['widgets']['star']=False
        old['geometry']['shadow']=[1580,62];old['notes']['2026-10-07']='Oma merkintä'
        atomic_json(self.path,old)
        loaded=State(self.path)
        self.assertEqual(loaded.settings['widget_text_scale'],130)
        self.assertEqual(loaded.settings['widget_clock_scale'],100)
        self.assertEqual(loaded.geometry('shadow'),[1580,62])
        self.assertFalse(loaded.settings['widgets']['star'])
        self.assertEqual(loaded.note(date(2026,10,7)),'Oma merkintä')

    def test_font_limits_and_durability(self):
        for changes in ({'widget_text_scale':79},{'widget_text_scale':161},{'widget_clock_scale':141},{'widget_text_scale':True}):
            with self.assertRaises(ValueError):self.state.configure(changes)
        self.state.configure({'widget_text_scale':150,'widget_clock_scale':120})
        loaded=State(self.path)
        self.assertEqual(loaded.settings['widget_text_scale'],150)
        self.assertEqual(loaded.settings['widget_clock_scale'],120)

    def test_note_and_reminder_are_shared_and_durable(self):
        day = date(2026, 10, 7)
        instant = datetime(2026, 10, 7, 18, tzinfo=timezone.utc)
        self.state.save_note(day, 'Sama tapahtuma kaikissa kalentereissa', instant)
        reloaded = State(self.path)
        self.assertEqual(reloaded.note(day), self.state.note(day))
        self.assertEqual(len(reloaded.take_due(instant)), 1)
        self.assertEqual(State(self.path).take_due(instant+timedelta(days=1)), [])
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_failed_write_does_not_change_memory_or_disk(self):
        self.state.configure({'opacity': 65})
        previous = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')):
            with self.assertRaises(OSError): self.state.configure({'opacity': 20})
        self.assertEqual(self.state.data, previous)
        self.assertEqual(self.path.read_bytes(), content)

    def test_settings_return_independent_copy(self):
        settings = self.state.settings; settings['widgets']['combined'] = False
        self.assertTrue(self.state.settings['widgets']['combined'])

    def test_invalid_settings_rejected(self):
        for change in ({'opacity': 101}, {'scale': True}, {'provider': 'unknown'}, {'widgets': {'spam': True}}, {'zone': 'Not/AZone'}):
            with self.assertRaises((ValueError, KeyError)): self.state.configure(change)
        self.assertEqual(self.state.settings, DEFAULTS)

    def test_invalid_reminder_rejected_atomically(self):
        with self.assertRaises(ValueError): self.state.save_note(date.today(), 'note', datetime.now())
        self.assertEqual(self.state.data['notes'], {})
        self.assertFalse(self.path.exists())

    def test_cancel_reminder_leaves_note(self):
        day=date(2026,10,7);instant=datetime(2026,10,7,18,tzinfo=timezone.utc)
        self.state.save_note(day,'Tapahtuma',instant)
        self.state.cancel_reminders([self.state.data['reminders'][0]['id']])
        self.assertEqual(State(self.path).data['reminders'],[])
        self.assertEqual(State(self.path).note(day),'Tapahtuma')

    def test_geometry_read_is_a_copy(self):
        self.state.geometry('weather', (20,30))
        result = self.state.geometry('weather');result[0] = 90
        self.assertEqual(self.state.geometry('weather'), [20,30])

    def test_legacy_import_read_only_and_idempotent(self):
        root = Path(self.directory.name)
        a = root/'Goottikalenteri/events.json'; b = root/'tahtiaika/state.json'
        atomic_json(a, {'events': {'0001-00-09': 'Varjon merkintä'}})
        atomic_json(b, {'events': {'fixed@2026-07-01:0001-03-08': 'Tähtimerkintä'}})
        before = (a.read_bytes(), b.read_bytes())
        with patch.dict(os.environ, {'XDG_DATA_HOME': str(root)}):
            self.state.import_legacy();self.state.import_legacy()
        self.assertEqual(self.state.note(date(2026,10,7)), 'Varjon merkintä\n\nTähtimerkintä')
        self.assertEqual(before, (a.read_bytes(), b.read_bytes()))
        self.assertEqual(self.state.data['imports'], ['legacy-v1'])
        self.assertTrue((root/'alkuperaiset-kalenterit.json').exists())


if __name__ == '__main__': unittest.main()
