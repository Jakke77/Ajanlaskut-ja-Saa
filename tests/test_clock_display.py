"""Independent clock modes, sparse digit sizes and atomic saved preferences."""
import copy
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from asaa.clock_config import PROFILE_KEYS
from asaa.clock_display import (CLOCK_DISPLAY_CHOICES, clock_digit_scale,
                               clock_display_selection, clock_mode)
from asaa.state import DEFAULTS, State, atomic_json
from asaa.theme import CALENDAR_THEMES, THEMES


class ClockDisplayStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix='ajanlaskut-clock-display-test-')
        self.path = Path(self.directory.name) / 'state.json'
        self.state = State(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_fresh_clocks_follow_their_theme_and_global_digit_size(self):
        self.assertEqual(self.state.settings['clock_displays'], {})
        self.assertFalse(self.path.exists())
        for key in PROFILE_KEYS:
            with self.subTest(clock=key):
                self.assertEqual(clock_display_selection(self.state.settings, key), {'mode': 'theme'})
                self.assertEqual(clock_digit_scale(self.state.settings, key), 100)
                self.assertEqual(clock_mode(self.state.settings, key, THEMES['copper']), 'digital')
                self.assertEqual(clock_mode(self.state.settings, key, THEMES['ubuntu']), 'both')

    def test_old_file_keeps_preferences_and_exact_bytes_without_display_overrides(self):
        old = copy.deepcopy(self.state.data)
        old['settings'].pop('clock_displays')
        old['settings'].update({'time_theme': 'ubuntu', 'widget_clock_scale': 123,
                                'widget_themes': {'star': 'calendar'}})
        old['settings']['clock_profiles']['star']['note'] = True
        old['notes']['2026-10-11'] = 'Oma merkintä'
        old['geometry']['combined'] = [520, 70]
        old['widget_sizes'] = {'combined': [430, 810]}
        self.path.write_text(json.dumps(old, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        content = self.path.read_bytes()
        loaded = State(self.path)
        expected = copy.deepcopy(old)
        expected['settings']['clock_displays'] = {}
        self.assertEqual(loaded.data, expected)
        self.assertEqual(self.path.read_bytes(), content)
        for key in PROFILE_KEYS:
            self.assertEqual(clock_display_selection(loaded.settings, key), {'mode': 'theme'})
            self.assertEqual(clock_digit_scale(loaded.settings, key), 123)

    def test_sparse_fields_and_all_modes_persist_without_normalizing_saved_maps(self):
        choices = {'combined': {'mode': 'digital'}, 'shadow': {'digit_scale': 80},
                   'star': {'mode': 'analog', 'digit_scale': 140}, 'civil': {}}
        self.state.configure({'clock_displays': choices})
        content = self.path.read_bytes()
        loaded = State(self.path)
        self.assertEqual(loaded.settings['clock_displays'], choices)
        self.assertEqual(self.path.read_bytes(), content)
        self.assertEqual(clock_display_selection(loaded.settings, 'shadow'),
                         {'mode': 'theme', 'digit_scale': 80})
        for mode in ('theme', 'digital', 'analog', 'both'):
            for key in PROFILE_KEYS:
                with self.subTest(clock=key, mode=mode):
                    selection = {key: {'mode': mode, 'digit_scale': 110}}
                    self.state.configure({'clock_displays': selection})
                    self.assertEqual(State(self.path).settings['clock_displays'], selection)

    def test_display_changes_preserve_profiles_and_other_widgets_and_content(self):
        self.state.save_note(date(2026, 10, 11), 'Säilyvä merkintä')
        self.state.configure({'theme': 'ubuntu', 'time_theme': 'calendar',
                              'widget_themes': {'combined': 'frost', 'weather': 'ubuntu'}})
        self.state.geometry('weather', [250, 100])
        before = copy.deepcopy(self.state.data)
        choices = {'combined': {'mode': 'analog'}, 'star': {'digit_scale': 130}}
        self.state.configure({'clock_displays': choices})
        expected = copy.deepcopy(before)
        expected['settings']['clock_displays'] = choices
        self.assertEqual(State(self.path).data, expected)
        for key in ('shadow', 'civil'):
            self.assertEqual(clock_display_selection(self.state.settings, key), {'mode': 'theme'})

    def test_invalid_maps_and_fields_do_not_change_memory_or_saved_file(self):
        self.state.configure({'clock_displays': {'combined': {'mode': 'analog', 'digit_scale': 120}}})
        before = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        invalid = [None, [], (), 'digital', True, 1,
                   {'unknown': {}}, {'weather': {'mode': 'digital'}},
                   {'combined': None}, {'combined': []}, {'combined': 'digital'},
                   {'combined': True}, {'combined': 1}, {'combined': {'unknown': 100}}]
        invalid.extend({'combined': {'mode': value}} for value in
                       ('', 'digits', None, True, 1, [], {}))
        invalid.extend({'combined': {'digit_scale': value}} for value in
                       (79, 141, True, False, 100.0, '100', None, [], {}))
        for choices in invalid:
            with self.subTest(choices=choices):
                with self.assertRaises(ValueError):
                    self.state.configure({'theme': 'ubuntu', 'clock_displays': choices})
                self.assertEqual(self.state.data, before)
                self.assertEqual(self.path.read_bytes(), content)

    def test_invalid_saved_display_map_is_rejected_without_rewriting_file(self):
        old = copy.deepcopy(self.state.data)
        old['settings']['clock_displays'] = {'star': {'digit_scale': True}}
        atomic_json(self.path, old)
        content = self.path.read_bytes()
        with self.assertRaises(ValueError):
            State(self.path)
        self.assertEqual(self.path.read_bytes(), content)

    def test_failed_write_keeps_previous_display_preferences(self):
        self.state.configure({'clock_displays': {'civil': {'mode': 'both'}}})
        before = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')):
            with self.assertRaises(OSError):
                self.state.configure({'clock_displays': {'civil': {'mode': 'digital'}}})
        self.assertEqual(self.state.data, before)
        self.assertEqual(self.path.read_bytes(), content)

    def test_inputs_snapshots_and_normalized_drafts_are_independent(self):
        choices = {'combined': {'mode': 'analog', 'digit_scale': 120},
                   'shadow': {'digit_scale': 90}}
        self.state.configure({'clock_displays': choices})
        choices['combined']['mode'] = 'digital'
        snapshot = self.state.settings
        snapshot['clock_displays']['shadow']['digit_scale'] = 140
        draft = clock_display_selection(self.state.settings, 'combined')
        draft.update({'mode': 'both', 'digit_scale': 140})
        expected = {'combined': {'mode': 'analog', 'digit_scale': 120},
                    'shadow': {'digit_scale': 90}}
        self.assertEqual(self.state.settings['clock_displays'], expected)
        self.assertEqual(State(self.path).settings['clock_displays'], expected)
        other = State(Path(self.directory.name) / 'another.json')
        self.assertEqual(other.settings['clock_displays'], {})
        self.assertEqual(DEFAULTS['clock_displays'], {})

    def test_removing_override_restores_global_size_without_changing_other_clock(self):
        self.state.configure({'widget_clock_scale': 110, 'clock_displays': {
            'combined': {'mode': 'analog', 'digit_scale': 140},
            'star': {'mode': 'digital', 'digit_scale': 80}}})
        choices = self.state.settings['clock_displays']
        choices.pop('combined')
        self.state.configure({'clock_displays': choices})
        loaded = State(self.path)
        self.assertEqual(clock_display_selection(loaded.settings, 'combined'), {'mode': 'theme'})
        self.assertEqual(clock_digit_scale(loaded.settings, 'combined'), 110)
        self.assertEqual(loaded.settings['clock_displays'],
                         {'star': {'mode': 'digital', 'digit_scale': 80}})


class ClockDisplayResolutionTests(unittest.TestCase):
    def setUp(self):
        self.options = copy.deepcopy(DEFAULTS)

    def test_missing_map_follows_effective_theme_and_global_digit_size(self):
        self.options.pop('clock_displays')
        self.options.update({'theme': 'ubuntu', 'time_theme': 'ubuntu', 'widget_clock_scale': 130})
        for key in PROFILE_KEYS:
            with self.subTest(clock=key):
                self.assertEqual(clock_display_selection(self.options, key), {'mode': 'theme'})
                self.assertEqual(clock_digit_scale(self.options, key), 130)
                for theme in (*THEMES.values(), *CALENDAR_THEMES.values()):
                    expected = 'both' if theme.motif == 'ubuntu' else 'digital'
                    self.assertEqual(clock_mode(self.options, key, theme), expected)

    def test_explicit_modes_are_independent_of_theme_and_calendar(self):
        for mode in ('digital', 'analog', 'both'):
            for key in PROFILE_KEYS:
                self.options['clock_displays'] = {key: {'mode': mode}}
                for theme in (*THEMES.values(), *CALENDAR_THEMES.values()):
                    with self.subTest(clock=key, mode=mode, motif=theme.motif):
                        self.assertEqual(clock_mode(self.options, key, theme), mode)

    def test_missing_digit_size_tracks_global_changes_while_explicit_size_stays_fixed(self):
        self.options['clock_displays'] = {'combined': {'mode': 'digital'},
                                        'shadow': {'digit_scale': 90}}
        for size in (80, 110, 140):
            self.options['widget_clock_scale'] = size
            self.assertEqual(clock_digit_scale(self.options, 'combined'), size)
            self.assertEqual(clock_digit_scale(self.options, 'shadow'), 90)
            self.assertEqual(clock_digit_scale(self.options, 'star'), size)
        self.assertEqual(clock_display_selection(self.options, 'combined'), {'mode': 'digital'})
        self.assertEqual(clock_display_selection(self.options, 'shadow'),
                         {'mode': 'theme', 'digit_scale': 90})

    def test_preview_is_a_complete_read_only_override_without_saved_field_leaks(self):
        self.options['clock_displays'] = {'combined': {'mode': 'analog', 'digit_scale': 140}}
        before = copy.deepcopy(self.options)
        for draft, expected_mode, expected_size in (
            ({}, 'both', 100), ({'mode': 'theme'}, 'both', 100),
            ({'mode': 'digital'}, 'digital', 100),
            ({'digit_scale': 80}, 'both', 80),
            ({'mode': 'both', 'digit_scale': 120}, 'both', 120),
        ):
            with self.subTest(draft=draft):
                draft_before = copy.deepcopy(draft)
                self.assertEqual(clock_mode(self.options, 'combined', THEMES['ubuntu'], draft), expected_mode)
                self.assertEqual(clock_digit_scale(self.options, 'combined', draft), expected_size)
                self.assertEqual(draft, draft_before)
        self.assertEqual(self.options, before)
        self.assertEqual(clock_mode(self.options, 'combined', THEMES['ubuntu']), 'analog')
        self.assertEqual(clock_digit_scale(self.options, 'combined'), 140)

    def test_choice_tokens_and_labels_are_the_display_contract(self):
        self.assertEqual(CLOCK_DISPLAY_CHOICES, [
            ('Teeman oletus', 'theme'), ('Digitaalinen', 'digital'),
            ('Analoginen', 'analog'), ('Analoginen ja digitaalinen', 'both'),
        ])


if __name__ == '__main__':
    unittest.main()
