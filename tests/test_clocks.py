import copy
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from asaa.clock_config import ClockRotation, DEFAULT_PROFILES, FIELD_LABELS, clock_layout
from asaa.state import State, DEFAULTS, atomic_json
from asaa import almanac

class RotationTests(unittest.TestCase):
    def setUp(self):
        self.now = 100
        self.options = copy.deepcopy(DEFAULTS)
        self.rotation = ClockRotation(self.options, monotonic=lambda:self.now, choose=lambda pool:pool[-1])
    def test_ordered_77_second_rotation(self):
        self.now += 76;self.assertFalse(self.rotation.poll())
        self.now += 1;self.assertTrue(self.rotation.poll());self.assertEqual(self.rotation.current,'star')
        self.now += 77;self.rotation.poll();self.assertEqual(self.rotation.current,'civil')
        self.now += 77;self.rotation.poll();self.assertEqual(self.rotation.current,'shadow')
    def test_fixed_never_switches_and_manual_steps_wrap(self):
        self.options.update(time_mode='fixed',time_system='civil');self.rotation.configure(self.options)
        self.now += 9000;self.assertFalse(self.rotation.poll());self.assertEqual(self.rotation.current,'civil')
        self.rotation.advance();self.assertEqual(self.rotation.current,'shadow')
    def test_random_excludes_the_current_calendar(self):
        self.options['time_mode']='random';self.rotation.configure(self.options)
        for _ in range(10):
            previous=self.rotation.current;self.rotation.advance();self.assertNotEqual(previous,self.rotation.current)
    def test_single_calendar_and_selected_subset(self):
        self.options.update(time_systems=['star'],time_mode='random');self.rotation.configure(self.options)
        self.assertEqual(self.rotation.current,'star');self.now += 77;self.assertFalse(self.rotation.poll())
        self.options.update(time_systems=['shadow','civil'],time_mode='cycle');self.rotation.configure(self.options)
        self.assertEqual(self.rotation.current,'shadow');self.rotation.advance();self.assertEqual(self.rotation.current,'civil')
    def test_appearance_does_not_restart_deadline(self):
        self.now += 70;self.options['widget_text_scale']=160;self.rotation.configure(self.options)
        self.assertEqual(self.rotation.remaining(),7)
    def test_sleep_resumes_without_a_burst(self):
        self.now += 10000;self.rotation.poll();self.assertEqual(self.rotation.current,'star')
        self.assertFalse(self.rotation.poll());self.assertEqual(self.rotation.remaining(),77)
    def test_hidden_fields_collapse_but_calendars_share_slots(self):
        profile=copy.deepcopy(DEFAULT_PROFILES['combined']);_,old=clock_layout(profile)
        profile['weather']=False;self.assertEqual(clock_layout(profile)[1],old-206)
        profile={key:False for key in FIELD_LABELS};profile['clock']=True
        self.assertEqual([block[0] for block in clock_layout(profile)[0]],['clock'])

class ClockStateTests(unittest.TestCase):
    def setUp(self):
        self.directory=TemporaryDirectory();self.path=Path(self.directory.name)/'state.json';self.state=State(self.path)
    def tearDown(self):self.directory.cleanup()
    def test_old_installation_does_not_enable_extra_windows(self):
        old=copy.deepcopy(self.state.data);settings=old['settings']
        for key in list(settings):
            if key.startswith('time_') or key.startswith('calendar_extra') or key=='clock_profiles':settings.pop(key)
        settings['widgets'].pop('combined');settings['widgets'].update(shadow=True,civil=True,star=False)
        settings['clock_weather']=False;old['geometry']['shadow']=[1572,49]
        old['notes']['2026-10-08']='Säilytä';atomic_json(self.path,old)
        loaded=State(self.path)
        self.assertFalse(loaded.settings['widgets']['combined']);self.assertTrue(loaded.settings['widgets']['civil'])
        self.assertFalse(loaded.settings['clock_profiles']['shadow']['weather'])
        self.assertEqual(loaded.note(date(2026,10,8)),'Säilytä');self.assertEqual(loaded.geometry('shadow'),[1572,49])
    def test_profile_and_visibility_settings_persist_independently(self):
        profiles=self.state.settings['clock_profiles'];profiles['combined']['note']=True;profiles['star']['weather']=True
        self.state.configure({'clock_profiles':profiles,'calendar_extras_visible':False,'calendar_extras':['hebrew','coptic']})
        loaded=State(self.path)
        self.assertTrue(loaded.settings['clock_profiles']['combined']['note']);self.assertFalse(loaded.settings['clock_profiles']['civil']['weather'])
        self.assertFalse(loaded.settings['calendar_extras_visible']);self.assertEqual(loaded.settings['calendar_extras'],['hebrew','coptic'])
    def test_legacy_weather_checkbox_bridge(self):
        self.state.configure({'clock_weather':False});self.assertFalse(self.state.settings['clock_profiles']['shadow']['weather'])
        profiles=self.state.settings['clock_profiles'];profiles['shadow']['weather']=True
        self.state.configure({'clock_profiles':profiles});self.assertTrue(self.state.settings['clock_weather'])
    def test_invalid_rotation_and_profiles_rejected_atomically(self):
        for changes in ({'time_mode':'unknown'},{'time_system':'fake'},{'time_interval':True},{'time_interval':0},
                        {'time_systems':[]},{'time_systems':['shadow','shadow']},{'time_theme':'fake'},
                        {'calendar_extras':['unknown']},{'calendar_extras':['hebrew','hebrew']},
                        {'calendar_extras_visible':1},{'calendar_extras_scope':'fake'},{'calendar_extra_cell':'fake'}):
            with self.assertRaises(ValueError):self.state.configure(changes)
        profiles=self.state.settings['clock_profiles'];profiles['combined']={key:False for key in FIELD_LABELS}
        with self.assertRaises(ValueError):self.state.configure({'clock_profiles':profiles})
        self.assertFalse(self.path.exists())

class AlmanacTests(unittest.TestCase):
    def test_known_new_year_dates(self):
        for key,civil,expected in [('hebrew',date(2023,9,16),(5784,7,1)),
            ('islamic',date(2023,7,19),(1445,1,1)),('persian',date(2024,3,20),(1403,1,1)),
            ('indian',date(2024,3,21),(1946,1,1)),('coptic',date(2023,9,12),(1740,1,1))]:
            item=almanac.convert(key,civil);self.assertEqual((item.year,item.month,item.day),expected,key)
    def test_julian_difference_is_not_always_13_days(self):
        item=almanac.convert('julian',date(2100,3,15));self.assertEqual((item.year,item.month,item.day),(2100,3,1))
    def test_roundtrips_leap_and_year_boundaries(self):
        for key,spec in almanac.SPECS.items():
            for civil in [date(1900,3,1),date(2000,2,29),date(2024,3,20),date(2026,10,8),date(2100,12,31)]:
                item=almanac.convert(key,civil);self.assertTrue(item.available,key)
                self.assertEqual(date(*spec.module.to_gregorian(item.year,item.month,item.day)),civil,key)
    def test_hidden_means_no_parallel_dates(self):
        options=copy.deepcopy(DEFAULTS);civil=date(2026,10,8)
        self.assertEqual(len(almanac.lines(options,'star',civil)),3)
        self.assertEqual(almanac.lines(options,'shadow',civil),[])
        options['calendar_extras_scope']='all';self.assertEqual(len(almanac.lines(options,'civil',civil)),3)
        options['calendar_extras_visible']=False;self.assertEqual(almanac.lines(options,'star',civil),[])
    def test_persian_unsupported_range_is_honest(self):
        self.assertFalse(almanac.convert('persian',date(9998,12,31)).available)
    def test_hebrew_leap_month_names(self):
        self.assertIn('Adar I',almanac.convert('hebrew',date(2024,2,15)).label)
        self.assertIn('Adar II',almanac.convert('hebrew',date(2024,3,15)).label)
