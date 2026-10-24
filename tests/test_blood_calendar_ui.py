"""Five-row Veri Aika calendar, actual dates, year edges and main navigation."""
from datetime import date, datetime, timedelta
import os
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import QObject, pyqtSignal, QEvent
from PyQt6.QtWidgets import QApplication

from asaa import blood_time
from asaa.blood_calendar_ui import BloodCalendarGrid


class GridController(QObject):
    notes_changed = pyqtSignal()
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.now = blood_time.EPOCH + timedelta(days=120)
        self.notes = {}
        self.calendars = SimpleNamespace(now=lambda: self.now)
        self.state = SimpleNamespace(note=lambda day: self.notes.get(day, ''))
        self.options = {'theme': 'blood'}


class BloodCalendarGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.controller = GridController()
        self.grid = BloodCalendarGrid(self.controller)
        self.grid.resize(700, 650)
        self.grid.show()
        self.app.processEvents()

    def tearDown(self):
        self.grid.close(); self.grid.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def test_23_pages_cover_the_777_days_once_in_seven_columns(self):
        shown = []
        for period in range(23):
            self.grid.set_day(blood_time.EPOCH_DATE + timedelta(days=period * 35))
            days = self.grid.visible_days
            self.assertEqual(len(days), 7 if period == 22 else 35)
            self.assertEqual(len(self.grid.day_buttons), len(days))
            for index, action in enumerate(self.grid.day_buttons):
                self.assertEqual(action.property('civil_date'), days[index])
                slot = self.grid.grid.indexOf(action)
                row, column, height, width = self.grid.grid.getItemPosition(slot)
                self.assertEqual((row, column, height, width), (1 + index // 7, index % 7, 1, 1))
            shown.extend(days)
        self.assertEqual(shown, [blood_time.EPOCH_DATE + timedelta(days=n) for n in range(777)])
        self.assertEqual(len(set(shown)), 777)
        self.assertIn('Viikot 111–111', self.grid.period.currentText())

    def test_page_and_year_navigation_follow_authored_year_boundaries(self):
        self.grid.set_day(blood_time.EPOCH_DATE + timedelta(days=770))
        self.grid.next.click()
        self.assertEqual(self.grid.selected, blood_time.EPOCH_DATE + timedelta(days=777))
        self.assertEqual(self.grid.period_index, 0)
        self.assertIn('0002', self.grid.year_heading.text())
        self.grid.previous.click()
        self.assertEqual(self.grid.selected, blood_time.EPOCH_DATE + timedelta(days=770))
        self.grid.set_day(blood_time.EPOCH_DATE + timedelta(days=120))
        names = blood_time.from_date(self.grid.selected).names
        self.grid.next_year.click()
        self.assertEqual(self.grid.selected, blood_time.EPOCH_DATE + timedelta(days=897))
        self.assertEqual(blood_time.from_date(self.grid.selected).names, names)
        self.assertEqual(self.grid.period_index, 3)

    def test_user_selection_reports_exact_date_and_note_without_storage_writes(self):
        self.grid.set_day(blood_time.EPOCH_DATE)
        day = blood_time.EPOCH_DATE + timedelta(days=29)
        self.controller.notes[day] = 'Säilyvä merkintä'
        self.controller.notes_changed.emit()
        selected = []
        self.grid.selected_changed.connect(selected.append)
        self.grid.set_day(blood_time.EPOCH_DATE)
        self.assertEqual(selected, [])
        self.grid.day_buttons[29].click()
        self.assertEqual(selected, [day])
        action = self.grid.day_buttons[29]
        self.assertTrue(action.isChecked())
        self.assertIn('•', action.text())
        self.assertIn('kalenterimerkintä', action.accessibleName())
        pair = blood_time.from_date(day).names
        self.assertIn(pair.male, action.toolTip())
        self.assertIn(pair.female, action.toolTip())
        self.assertIn('Säilyvä merkintä', action.toolTip())
        self.assertEqual(action.accessibleDescription(), action.toolTip())
        self.assertEqual(self.controller.notes, {day: 'Säilyvä merkintä'})

    def test_today_uses_finnish_cutover_and_pre_epoch_grid_is_explicit(self):
        self.controller.now = blood_time.EPOCH + timedelta(days=7, seconds=-1)
        self.grid.today_button.click()
        self.assertEqual(self.grid.selected, date(2026, 7, 2))
        self.controller.now += timedelta(seconds=1)
        self.grid.today_button.click()
        self.assertEqual(self.grid.selected, date(2026, 7, 3))
        self.grid.set_day(date(1985, 2, 14))
        self.assertIn('ENNEN VERI AJAN ALKUA', self.grid.year_heading.text())
        self.assertNotIn('VUOSI 0000', self.grid.year_heading.text())
        self.assertIn(date(1985, 2, 14), self.grid.visible_days)

    def test_date_limits_do_not_offer_selectable_dates_outside_supported_years(self):
        for day in (date(1900, 1, 1), date(2100, 12, 31)):
            self.grid.set_day(day)
            for action in self.grid.day_buttons:
                civil = action.property('civil_date')
                self.assertEqual(action.isEnabled(), date(1900, 1, 1) <= civil <= date(2100, 12, 31))
        for invalid in (date(1899, 12, 31), date(2101, 1, 1), datetime(2026, 6, 26), '2026-06-26'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.grid.set_day(invalid)


if __name__ == '__main__':
    unittest.main()
