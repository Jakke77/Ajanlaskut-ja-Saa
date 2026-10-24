"""Actual Qt interactions for the uninterrupted week and live sky views."""
from datetime import date, datetime, timedelta
import os
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import QObject, QDate, QRectF, pyqtSignal
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

from asaa.blood_ui import VeriPage
from asaa.otava_ui import OtavaView, paint_otava
from asaa.theme import THEMES
from asaa import blood_time


class MemoryController(QObject):
    clock_changed = pyqtSignal()
    settings_changed = pyqtSignal()
    notes_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.now = datetime(2026, 10, 24, 15, 30, tzinfo=ZoneInfo('Europe/Helsinki'))
        self.calendars = SimpleNamespace(now=lambda: self.now)
        self.options = {'theme': 'copper'}
        self.state = SimpleNamespace(note=lambda day: '')
        self.opened = None

    def open_calendar(self, system, day):
        self.opened = system, day


class VeriUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.controller = MemoryController()
        self.page = VeriPage(self.controller)
        self.page.resize(810, 1000)

    def tearDown(self):
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    def test_real_week_navigation_keeps_selected_week_while_clock_ticks(self):
        self.page.set_day(date(2026, 6, 26))
        self.assertEqual(self.page.week_start, date(2026, 6, 26))
        self.assertIn('1. VIIKKO', self.page.week_heading.text())
        self.assertEqual(len(self.page.day_buttons), 7)
        self.page.next.click()
        self.assertEqual(self.page.selected, date(2026, 7, 3))
        self.assertIn('2. VIIKKO', self.page.week_heading.text())
        self.controller.now += timedelta(days=2)
        self.controller.clock_changed.emit()
        self.assertEqual(self.page.selected, date(2026, 7, 3))
        self.assertEqual(self.page.sky.moment, self.controller.now)
        self.page.day_buttons[5].click()
        self.assertEqual(self.page.selected, date(2026, 7, 8))
        self.page.open_day.click()
        self.assertEqual(self.controller.opened, ('civil', date(2026, 7, 8)))

    def test_now_tracks_the_cutover_and_week_at_exact_second(self):
        self.controller.now = blood_time.EPOCH + timedelta(days=7, seconds=-1)
        self.page.today_button.click()
        self.assertEqual(self.page.selected, date(2026, 7, 2))
        self.assertIn('7. päivä · 1. viikko', self.page.current.text())
        self.controller.now += timedelta(seconds=1)
        self.controller.clock_changed.emit()
        self.assertEqual(self.page.selected, date(2026, 7, 3))
        self.assertIn('1. päivä · 2. viikko', self.page.current.text())
        self.assertIn('10.07.2026 01:07:07', self.page.next_change.text())

    def test_date_selection_does_not_change_live_sky_to_a_historical_time(self):
        self.page.date.setDate(QDate(1980, 1, 2))
        self.assertEqual(self.page.selected, date(1980, 1, 2))
        self.assertIn('ENNEN VERI AJAN ALKUA', self.page.week_heading.text())
        self.assertEqual(self.page.sky.moment, self.controller.now)
        self.assertIn('symbolinen', self.page.rules.text())
        self.assertIn('Suomen paikallista aikaa', self.page.rules.text())

    def test_seven_actual_stars_render_and_accessibility_reports_directions(self):
        view = self.page.sky
        view.resize(650, 340)
        picture = view.grab()
        self.assertFalse(picture.isNull())
        self.assertEqual(len(view.sky), 7)
        self.assertEqual(len(view.drawn_points), 7)
        for name in ('Dubhe', 'Merak', 'Phecda', 'Megrez', 'Alioth', 'Mizar', 'Alkaid'):
            self.assertIn(name, view.accessibleName())
        self.assertIn('korkeus', view.toolTip())
        self.assertIn('taivaannapa', view.accessibleName())

    def test_projection_changes_with_time_without_changing_painter_state(self):
        image = QImage(320, 320, QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        rect = QRectF(10, 10, 300, 300)
        original = painter.transform()
        first = paint_otava(painter, rect, self.controller.now, THEMES['copper'])
        second = paint_otava(painter, rect, self.controller.now + timedelta(hours=6), THEMES['copper'])
        self.assertEqual(painter.transform(), original)
        painter.end()
        self.assertEqual(len(first), 7)
        self.assertTrue(all(rect.contains(point) for point in first + second))
        self.assertTrue(any((a - b).manhattanLength() > 20 for a, b in zip(first, second)))

    def test_invalid_timestamp_is_an_accessible_error_not_a_widget_crash(self):
        view = OtavaView(self.controller, compact=True)
        view.set_moment(datetime(2026, 10, 24))
        self.assertEqual(view.sky, ())
        self.assertIn('ei voida laskea', view.accessibleName())
        self.assertFalse(view.grab().isNull())
        view.close()
        view.deleteLater()


if __name__ == '__main__':
    unittest.main()
