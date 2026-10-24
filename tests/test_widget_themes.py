"""Sparse widget overrides, legacy appearance and atomic saved preferences."""
import copy
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from asaa.clock_config import PROFILE_KEYS, SYSTEMS
from asaa.state import DEFAULTS, State, atomic_json
from asaa.theme import CALENDAR_THEMES, THEMES
from asaa.widget_themes import widget_theme, widget_theme_choices, widget_theme_selection


class WidgetThemeStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix='ajanlaskut-widget-theme-test-')
        self.path = Path(self.directory.name) / 'state.json'
        self.state = State(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_fresh_widgets_follow_the_shared_theme(self):
        self.assertEqual(self.state.settings['time_theme'], 'shared')
        self.assertEqual(self.state.settings['widget_themes'], {})
        self.assertFalse(self.path.exists())
        self.state.configure({'theme': 'ubuntu'})
        for key in DEFAULTS['widgets']:
            with self.subTest(widget=key):
                self.assertEqual(widget_theme_selection(self.state.settings, key), 'shared')
                self.assertEqual(widget_theme(self.state.settings, key, 'civil'), THEMES['ubuntu'])

    def test_dark_ubuntu_can_be_saved_independently_for_shared_and_clock_themes(self):
        self.state.configure({'theme': 'ubuntu2610_dark', 'time_theme': 'calendar',
                              'widget_themes': {'weather': 'ubuntu2610_dark', 'combined': 'ubuntu'}})
        loaded = State(self.path)
        self.assertEqual(loaded.settings['theme'], 'ubuntu2610_dark')
        self.assertEqual(widget_theme(loaded.settings, 'weather'), THEMES['ubuntu2610_dark'])
        self.assertEqual(widget_theme(loaded.settings, 'combined', 'civil'), THEMES['ubuntu'])
        self.assertEqual(widget_theme(loaded.settings, 'star', 'star'), CALENDAR_THEMES['star'])
        loaded.configure({'time_theme': 'ubuntu2610_dark'})
        reopened = State(self.path)
        self.assertEqual(widget_theme(reopened.settings, 'star', 'star'), THEMES['ubuntu2610_dark'])
        self.assertEqual(widget_theme(reopened.settings, 'combined', 'civil'), THEMES['ubuntu'])

    def test_legacy_missing_clock_theme_keeps_calendar_palettes_without_rewriting(self):
        old = copy.deepcopy(self.state.data)
        old['settings'].pop('time_theme')
        old['settings'].pop('widget_themes')
        old['settings']['theme'] = 'frost'
        old['settings']['widgets']['star'] = True
        old['notes']['2026-10-07'] = 'Vanha merkintä'
        old['geometry']['combined'] = [700, 50]
        old['widget_sizes'] = {'combined': [430, 610]}
        atomic_json(self.path, old)
        content = self.path.read_bytes()
        loaded = State(self.path)
        expected = copy.deepcopy(old)
        expected['settings'].update({'time_theme': 'calendar', 'widget_themes': {}})
        self.assertEqual(loaded.data, expected)
        self.assertEqual(self.path.read_bytes(), content)
        for key in PROFILE_KEYS:
            self.assertEqual(widget_theme_selection(loaded.settings, key), 'calendar')
        self.assertEqual(widget_theme(loaded.settings, 'star', 'star'), CALENDAR_THEMES['star'])

    def test_legacy_explicit_clock_preferences_remain_unchanged(self):
        for selection in ('calendar', 'shared', 'ubuntu'):
            with self.subTest(clock_theme=selection):
                old = copy.deepcopy(self.state.data)
                old['settings']['time_theme'] = selection
                old['settings'].pop('widget_themes')
                atomic_json(self.path, old)
                content = self.path.read_bytes()
                loaded = State(self.path)
                self.assertEqual(loaded.settings['time_theme'], selection)
                self.assertEqual(loaded.settings['widget_themes'], {})
                self.assertEqual(self.path.read_bytes(), content)

    def test_sparse_overrides_persist_and_do_not_change_other_preferences(self):
        self.state.save_note(date(2026, 10, 7), 'Oma merkintä')
        self.state.geometry('weather', [100, 200])
        before = copy.deepcopy(self.state.data)
        choices = {'combined': 'ubuntu', 'weather': 'frost', 'star': 'calendar'}
        self.state.configure({'widget_themes': choices})
        expected = copy.deepcopy(before)
        expected['settings']['widget_themes'] = choices
        self.assertEqual(State(self.path).data, expected)
        self.assertEqual(widget_theme_selection(self.state.settings, 'shadow'), 'shared')
        self.assertEqual(widget_theme_selection(self.state.settings, 'weather'), 'frost')

    def test_invalid_overrides_leave_memory_and_file_unchanged(self):
        self.state.save_note(date(2026, 10, 7), 'Merkintä säilyy')
        self.state.configure({'widget_themes': {'combined': 'ubuntu', 'weather': 'frost'}})
        before = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        invalid = [None, [], 'ubuntu', {'unknown': 'ubuntu'}, {'combined': 'unknown'},
                   {'combined': None}, {'combined': True}, {'combined': 1},
                   {'combined': []}, {'combined': {}}, {'combined': ''}]
        invalid.extend({key: 'calendar'} for key in DEFAULTS['widgets'] if key not in PROFILE_KEYS)
        for choices in invalid:
            with self.subTest(choices=choices):
                with self.assertRaises(ValueError):
                    self.state.configure({'theme': 'frost', 'widget_themes': choices})
                self.assertEqual(self.state.data, before)
                self.assertEqual(self.path.read_bytes(), content)

    def test_failed_override_write_keeps_the_previous_selection(self):
        self.state.configure({'widget_themes': {'weather': 'frost'}})
        before = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')):
            with self.assertRaises(OSError):
                self.state.configure({'widget_themes': {'weather': 'ubuntu'}})
        self.assertEqual(self.state.data, before)
        self.assertEqual(self.path.read_bytes(), content)

    def test_override_maps_and_inputs_are_independent_copies(self):
        choices = {'combined': 'ubuntu', 'weather': 'frost'}
        self.state.configure({'widget_themes': choices})
        choices['weather'] = 'copper'
        snapshot = self.state.settings
        snapshot['widget_themes']['combined'] = 'shared'
        self.assertEqual(self.state.settings['widget_themes'], {'combined': 'ubuntu', 'weather': 'frost'})
        self.assertEqual(State(self.path).settings['widget_themes'], self.state.settings['widget_themes'])
        self.assertEqual(State(Path(self.directory.name) / 'another.json').settings['widget_themes'], {})
        self.assertEqual(DEFAULTS['widget_themes'], {})

    def test_removing_one_override_restores_its_fallback_and_keeps_the_other(self):
        self.state.configure({'time_theme': 'calendar',
                              'widget_themes': {'combined': 'ubuntu', 'weather': 'frost'}})
        choices = self.state.settings['widget_themes']
        choices.pop('combined')
        self.state.configure({'widget_themes': choices})
        loaded = State(self.path)
        self.assertEqual(loaded.settings['widget_themes'], {'weather': 'frost'})
        self.assertEqual(widget_theme_selection(loaded.settings, 'combined'), 'calendar')
        self.assertEqual(widget_theme(loaded.settings, 'weather'), THEMES['frost'])


class WidgetThemeResolutionTests(unittest.TestCase):
    def setUp(self):
        self.options = copy.deepcopy(DEFAULTS)

    def test_absent_map_uses_legacy_clock_selection_and_shared_other_widgets(self):
        self.options.pop('widget_themes')
        self.options.update({'theme': 'frost', 'time_theme': 'calendar'})
        for key in DEFAULTS['widgets']:
            with self.subTest(widget=key):
                if key in PROFILE_KEYS:
                    self.assertEqual(widget_theme_selection(self.options, key), 'calendar')
                    for system in SYSTEMS:
                        self.assertEqual(widget_theme(self.options, key, system), CALENDAR_THEMES[system])
                else:
                    self.assertEqual(widget_theme_selection(self.options, key), 'shared')
                    self.assertEqual(widget_theme(self.options, key), THEMES['frost'])

    def test_explicit_shared_overrides_a_legacy_ubuntu_clock_preference(self):
        self.options.update({'theme': 'frost', 'time_theme': 'ubuntu',
                             'widget_themes': {'combined': 'shared'}})
        self.assertEqual(widget_theme(self.options, 'combined', 'shadow'), THEMES['frost'])
        self.assertEqual(widget_theme(self.options, 'shadow', 'shadow'), THEMES['ubuntu'])
        self.assertEqual(widget_theme(self.options, 'weather'), THEMES['frost'])

    def test_explicit_palettes_stay_fixed_as_global_theme_and_calendar_change(self):
        for selection in THEMES:
            for key in DEFAULTS['widgets']:
                self.options['widget_themes'] = {key: selection}
                for global_theme in THEMES:
                    self.options['theme'] = global_theme
                    for system in SYSTEMS:
                        with self.subTest(widget=key, selection=selection, global_theme=global_theme, system=system):
                            self.assertEqual(widget_theme(self.options, key, system), THEMES[selection])

    def test_preview_selection_does_not_change_saved_override(self):
        self.options['widget_themes'] = {'combined': 'ubuntu'}
        before = copy.deepcopy(self.options)
        self.assertEqual(widget_theme(self.options, 'combined', 'star', selection='calendar'), CALENDAR_THEMES['star'])
        self.assertEqual(widget_theme(self.options, 'combined', 'star', selection='shared'), THEMES['copper'])
        self.assertEqual(self.options, before)
        self.assertEqual(widget_theme_selection(self.options, 'combined'), 'ubuntu')

    def test_picker_choices_offer_calendar_only_for_clock_widgets(self):
        for key in DEFAULTS['widgets']:
            with self.subTest(widget=key):
                choices = widget_theme_choices(key)
                labels = {token: label for label, token in choices}
                expected = {'shared', 'copper', 'frost', 'ubuntu', 'ubuntu2610_dark', 'blood'}
                if key in PROFILE_KEYS:
                    expected.add('calendar')
                    self.assertEqual(labels['ubuntu'], 'Ubuntu · oranssi ja munakoiso')
                else:
                    self.assertEqual(labels['ubuntu'], 'Ubuntu · oranssi ja munakoiso')
                self.assertEqual(set(labels), expected)
                self.assertEqual(labels['ubuntu2610_dark'], 'Ubuntu 26.10 Dark')
                self.assertEqual(labels['blood'], 'Veriyö')
                self.assertEqual(choices[0], ('Sovelluksen yhteinen teema', 'shared'))
                choices.clear()
                self.assertTrue(widget_theme_choices(key))


if __name__ == '__main__':
    unittest.main()
