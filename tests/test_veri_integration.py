"""Veri Aika reaches real menus, persisted settings and rendered desktop clocks."""
import copy
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication
from asaa.app import Controller
from asaa.state import State, atomic_json
from asaa.clock_config import FIELD_LABELS, PROFILE_KEYS
from tests.test_about import MemoryTray
from tests.test_icon_ui import MemoryIcons
from tests.test_wallpapers import MemoryBackend


class VeriIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='asaa-veri-')
        self.root = Path(self.directory.name)
        self.environment = patch.dict(os.environ, {'XDG_DATA_HOME': str(self.root/'data')})
        self.environment.start()
        self.tray = patch('asaa.app.QSystemTrayIcon', MemoryTray)
        self.tray.start()
        self.state = State(self.root/'state.json')
        self.controller = Controller(self.app, self.state, network=False,
            wallpaper_backend=MemoryBackend(), icon_backend=MemoryIcons())
        self.controller.tick_timer.stop()
        self.now = datetime(2026, 7, 3, 1, 7, 6, tzinfo=ZoneInfo('Europe/Helsinki'))
        self.controller.calendars.now = lambda: self.now

    def tearDown(self):
        self.controller.shutdown()
        self.controller.window.hide(); self.controller.window.deleteLater()
        for widget in self.controller.widgets.values():
            widget.hide(); widget.deleteLater()
        self.controller.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete); self.app.processEvents()
        self.tray.stop(); self.environment.stop(); self.directory.cleanup()

    def test_old_three_calendar_settings_migrate_without_changing_selected_cycle(self):
        old = copy.deepcopy(self.state.data)
        settings = old['settings']
        settings['time_systems'] = ['shadow', 'star', 'civil']
        settings['widgets'].pop('blood')
        settings['clock_profiles'].pop('blood')
        for profile in settings['clock_profiles'].values():
            profile.pop('otava')
            profile.pop('nameday')
        old['notes']['2026-10-24'] = 'Säilytä merkintä'
        old['geometry']['combined'] = [180, 40]
        atomic_json(self.state.path, old)
        migrated = State(self.state.path)
        self.assertEqual(migrated.settings['time_systems'], ['shadow', 'star', 'civil'])
        self.assertFalse(migrated.settings['widgets']['blood'])
        self.assertEqual(set(migrated.settings['clock_profiles']), set(PROFILE_KEYS))
        self.assertTrue(migrated.settings['clock_profiles']['blood']['otava'])
        self.assertTrue(migrated.settings['clock_profiles']['combined']['otava'])
        self.assertTrue(migrated.settings['clock_profiles']['blood']['nameday'])
        self.assertTrue(migrated.settings['clock_profiles']['combined']['nameday'])
        self.assertEqual(migrated.note(date(2026, 10, 24)), 'Säilytä merkintä')
        self.assertEqual(migrated.geometry('combined'), [180, 40])

    def test_menu_calendar_selector_and_overview_use_actual_cutover(self):
        controller = self.controller
        self.assertIn('blood', controller.window.navigation)
        overview = controller.window.page_widgets['overview']
        overview.tick()
        self.assertEqual(overview.date_labels['blood'].text(), '7. päivä · 1. viikko · vuosi 0001')
        self.now = self.now.replace(second=7)
        controller.clock_changed.emit()
        self.assertEqual(overview.date_labels['blood'].text(), '1. päivä · 2. viikko · vuosi 0001')
        controller.open_calendar('blood')
        self.assertTrue(controller.window.navigation['blood'].isChecked())
        calendar = controller.window.page_widgets['calendar']
        calendar.set_day('civil', date(2026, 6, 26))
        calendar.selector.setCurrentIndex(calendar.selector.findData('blood'))
        page = controller.window.page_widgets['blood']
        self.assertEqual(page.selected, date(2026, 6, 26))
        self.assertEqual(calendar.selector.currentData(), 'civil')
        self.assertIn('1. VIIKKO', page.week_heading.text())
        self.assertIn('0001', page.week_heading.text())
        self.assertEqual(len(overview.otava.sky), 7)

    def test_otava_mode_roundtrip_and_real_sky_content_are_independent(self):
        controller = self.controller
        controller.set_widget('combined', True)
        controller.select_time('blood')
        widget = controller.widgets['combined']
        for mode in ('otava', 'otava_both'):
            controller.configure({'clock_displays': {'combined': {'mode': mode}}})
            self.app.processEvents()
            self.assertTrue(widget.analog_clock)
            self.assertEqual(widget.digital_clock, mode == 'otava_both')
            self.assertFalse(widget.grab().isNull())
            values = [row[0] for row in widget.text_layout]
            self.assertIn('7. päivä · 1. viikko · vuosi 0001', values)
            self.assertTrue(any(value.startswith('Otava · Oulu') for value in values))
            self.assertIn('symbolinen sekuntiviisari', widget.toolTip())
            self.assertEqual(State(self.state.path).settings['clock_displays']['combined']['mode'], mode)
        self.now = self.now.replace(second=7)
        controller.clock_changed.emit(); widget.grab()
        self.assertIn('1. päivä · 2. viikko · vuosi 0001', [row[0] for row in widget.text_layout])

    def test_all_fields_fit_and_physical_sky_can_be_disabled_separately(self):
        controller = self.controller
        profiles = controller.options['clock_profiles']
        profiles['blood'] = {key: True for key in FIELD_LABELS}
        controller.configure({'clock_profiles': profiles, 'widget_text_scale': 160,
            'opacity': 0, 'clock_displays': {'blood': {'mode': 'otava_both'}}})
        controller.set_widget('blood', True)
        widget = controller.widgets['blood']
        self.assertFalse(widget.grab().isNull())
        for _, rect, _, ink_height, ink_width in widget.text_layout:
            self.assertLessEqual(ink_height, rect.height()+.1)
            self.assertLessEqual(ink_width, rect.width()+1)
            self.assertGreaterEqual(rect.top(), 0)
            self.assertLessEqual(rect.bottom(), widget.logical_height+.1)
        for index, (_, rect, *_) in enumerate(widget.text_layout):
            self.assertFalse(any(rect.intersects(other[1]) for other in widget.text_layout[index+1:]))
        profiles['blood']['otava'] = False
        controller.configure({'clock_profiles': profiles})
        widget.grab()
        self.assertFalse(any(row[0].startswith('Otava · Oulu') for row in widget.text_layout))
        self.assertTrue(widget.analog_clock)

    def test_blood_clock_uses_finnish_cutover_when_display_timezone_is_elsewhere(self):
        controller = self.controller
        controller.configure({'zone': 'America/New_York'})
        self.now = datetime(2026, 7, 2, 18, 7, 7, tzinfo=ZoneInfo('America/New_York'))
        controller.calendars.now = lambda: self.now
        controller.set_widget('blood', True)
        widget = controller.widgets['blood']; widget.grab()
        self.assertIn('1. päivä · 2. viikko · vuosi 0001', [row[0] for row in widget.text_layout])
        self.assertTrue(any('EEST' in row[0] for row in widget.text_layout if row[0].startswith('Otava · Oulu')))

    def test_year_and_name_pair_roll_over_together_without_resizing_clock(self):
        from asaa import blood_time as blood
        from asaa.blood_names import names_at
        controller = self.controller
        boundary = blood.boundary(blood.EPOCH_DATE + timedelta(days=777))
        self.now = boundary - timedelta(seconds=1)
        controller.set_widget('blood', True)
        widget = controller.widgets['blood']
        widget.grab()
        size = widget.size()
        values = [row[0] for row in widget.text_layout]
        self.assertIn('7. päivä · 111. viikko · vuosi 0001', values)
        self.assertIn('Mies: '+names_at(777).male, values)
        self.assertIn('Nainen: '+names_at(777).female, values)
        self.now = boundary
        controller.clock_changed.emit(); widget.grab()
        values = [row[0] for row in widget.text_layout]
        self.assertIn('1. päivä · 1. viikko · vuosi 0002', values)
        self.assertIn('Mies: '+names_at(1).male, values)
        self.assertIn('Nainen: '+names_at(1).female, values)
        self.assertEqual(widget.size(), size)
        overview = controller.window.page_widgets['overview']
        self.assertIn('Vuoden päivä 1/777', overview.note_labels['blood'].text())
        self.assertIn(names_at(1).male, overview.note_labels['blood'].text())

    def test_names_field_can_be_hidden_and_its_choice_survives_restart(self):
        controller = self.controller
        controller.set_widget('blood', True)
        widget = controller.widgets['blood']; widget.grab()
        self.assertTrue(any(row[0].startswith('Mies: ') for row in widget.text_layout))
        profiles = controller.options['clock_profiles']; profiles['blood']['nameday'] = False
        controller.configure({'clock_profiles': profiles})
        widget.grab()
        self.assertFalse(any(row[0].startswith(('Mies: ', 'Nainen: ')) for row in widget.text_layout))
        self.assertFalse(State(self.state.path).settings['clock_profiles']['blood']['nameday'])

    def test_blood_note_follows_effective_day_before_cutover(self):
        controller = self.controller
        controller.state.save_note(date(2026, 7, 2), 'Edellisen alkupäivän merkintä')
        controller.state.save_note(date(2026, 7, 3), 'Uuden alkupäivän merkintä')
        profiles = controller.options['clock_profiles']; profiles['blood']['note'] = True
        controller.configure({'clock_profiles': profiles})
        controller.set_widget('blood', True)
        widget = controller.widgets['blood']; widget.grab()
        self.assertIn('Edellisen alkupäivän merkintä', [row[0] for row in widget.text_layout])
        self.now = self.now.replace(second=7)
        controller.clock_changed.emit(); widget.grab()
        self.assertIn('Uuden alkupäivän merkintä', [row[0] for row in widget.text_layout])


if __name__ == '__main__':
    unittest.main()
