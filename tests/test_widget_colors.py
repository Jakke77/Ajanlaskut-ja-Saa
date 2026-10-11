"""Sparse text colors for all eight widgets and atomic preference persistence."""
import copy
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from asaa.state import DEFAULTS, State
from asaa.widget_colors import widget_text_color_selection


class WidgetColorStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix='ajanlaskut-widget-color-test-')
        self.path = Path(self.directory.name) / 'state.json'
        self.state = State(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_fresh_widgets_have_no_custom_text_colors(self):
        self.assertEqual(self.state.settings['widget_text_colors'], {})
        self.assertFalse(self.path.exists())
        for key in DEFAULTS['widgets']:
            self.assertIsNone(widget_text_color_selection(self.state.settings, key))
        old_options = self.state.settings
        old_options.pop('widget_text_colors')
        before = copy.deepcopy(old_options)
        for key in DEFAULTS['widgets']:
            self.assertIsNone(widget_text_color_selection(old_options, key))
        self.assertEqual(old_options, before)

    def test_old_file_gains_only_empty_color_map_without_rewriting_preferences(self):
        old = copy.deepcopy(self.state.data)
        old['settings'].pop('widget_text_colors')
        old['settings'].update({'theme': 'ubuntu', 'time_theme': 'calendar',
                                'widget_themes': {'star': 'frost', 'weather': 'ubuntu'},
                                'clock_displays': {'combined': {'mode': 'digital', 'digit_color': '#aBcDeF'},
                                                   'shadow': {'digit_scale': 120}}})
        old['settings']['clock_profiles']['combined']['note'] = True
        old['notes']['2026-10-11'] = 'Oma merkintä'
        old['geometry']['weather'] = [420, 50]
        old['widget_sizes'] = {'weather': [540, 320]}
        self.path.write_text(json.dumps(old, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        content = self.path.read_bytes()
        loaded = State(self.path)
        expected = copy.deepcopy(old)
        expected['settings']['widget_text_colors'] = {}
        self.assertEqual(loaded.data, expected)
        self.assertEqual(self.path.read_bytes(), content)

    def test_all_eight_colors_persist_without_changing_themes_clock_knobs_or_content(self):
        self.state.save_note(date(2026, 10, 11), 'Säilyvä merkintä')
        self.state.configure({'widget_themes': {'weather': 'frost'},
                              'clock_displays': {'combined': {'digit_color': '#010203', 'mode': 'digital'}}})
        self.state.geometry('star_calendar', [600, 90])
        before = copy.deepcopy(self.state.data)
        choices = dict(zip(DEFAULTS['widgets'],
                           ('#000000', '#ffffff', '#aBcDeF', '#123456',
                            '#FFFFFF', '#abcdef', '#808080', '#ABCDEF')))
        self.assertEqual(len(choices), 8)
        self.state.configure({'widget_text_colors': choices})
        expected = copy.deepcopy(before)
        expected['settings']['widget_text_colors'] = choices
        loaded = State(self.path)
        self.assertEqual(loaded.data, expected)
        for key, color in choices.items():
            self.assertEqual(widget_text_color_selection(loaded.settings, key), color)
        self.assertEqual(loaded.settings['clock_displays']['combined']['digit_color'], '#010203')

    def test_sparse_colors_stay_sparse_and_removing_one_keeps_the_other(self):
        choices = {'weather': '#aBcDeF', 'combined': '#123456'}
        self.state.configure({'widget_text_colors': choices})
        content = self.path.read_bytes()
        loaded = State(self.path)
        self.assertEqual(loaded.settings['widget_text_colors'], choices)
        self.assertEqual(self.path.read_bytes(), content)
        choices = loaded.settings['widget_text_colors']
        choices.pop('combined')
        loaded.configure({'widget_text_colors': choices})
        reloaded = State(self.path)
        self.assertEqual(reloaded.settings['widget_text_colors'], {'weather': '#aBcDeF'})
        self.assertIsNone(widget_text_color_selection(reloaded.settings, 'combined'))
        self.assertEqual(widget_text_color_selection(reloaded.settings, 'weather'), '#aBcDeF')

    def test_invalid_colors_or_maps_leave_memory_and_file_unchanged(self):
        self.state.configure({'widget_text_colors': {'weather': '#aBcDeF'}})
        before = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        invalid = [None, [], (), '#123456', True, 1, {'unknown': '#123456'},
                   {'main': '#123456'}, {1: '#123456'}]
        bad_colors = ('', '#abc', '#12345', '#1234567', '#ff123456', '123456',
                      '#12345g', 'red', ' #123456', '#123456\n', '#１２３４５６',
                      None, True, False, 123456, 100.0, [], {})
        invalid.extend({key: color} for key in DEFAULTS['widgets'] for color in bad_colors)
        for choices in invalid:
            with self.subTest(choices=choices):
                with self.assertRaises(ValueError):
                    self.state.configure({'theme': 'ubuntu', 'widget_text_colors': choices})
                self.assertEqual(self.state.data, before)
                self.assertEqual(self.path.read_bytes(), content)

    def test_failed_color_write_keeps_previous_selection(self):
        self.state.configure({'widget_text_colors': {'daily': '#808080'}})
        before = copy.deepcopy(self.state.data)
        content = self.path.read_bytes()
        with patch('asaa.state.atomic_json', side_effect=OSError('Levy täynnä')):
            with self.assertRaises(OSError):
                self.state.configure({'widget_text_colors': {'daily': '#ffffff'}})
        self.assertEqual(self.state.data, before)
        self.assertEqual(self.path.read_bytes(), content)

    def test_color_inputs_and_settings_copies_are_independent(self):
        choices = {'weather': '#aBcDeF', 'combined': '#808080'}
        self.state.configure({'widget_text_colors': choices})
        choices['weather'] = '#ffffff'
        snapshot = self.state.settings
        snapshot['widget_text_colors']['combined'] = '#000000'
        before = copy.deepcopy(self.state.settings)
        self.assertEqual(widget_text_color_selection(self.state.settings, 'weather'), '#aBcDeF')
        self.assertEqual(self.state.settings, before)
        expected = {'weather': '#aBcDeF', 'combined': '#808080'}
        self.assertEqual(self.state.settings['widget_text_colors'], expected)
        self.assertEqual(State(self.path).settings['widget_text_colors'], expected)
        other = State(Path(self.directory.name) / 'another.json')
        self.assertEqual(other.settings['widget_text_colors'], {})
        self.assertEqual(DEFAULTS['widget_text_colors'], {})


if __name__ == '__main__':
    unittest.main()
