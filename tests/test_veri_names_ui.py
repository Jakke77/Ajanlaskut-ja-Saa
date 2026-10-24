"""Real calendar and birthday lookup share the 777 fixed Veri Aika name pairs."""
import copy
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QDate, QEvent
from PyQt6.QtWidgets import QApplication

from asaa.app import Controller
from asaa.state import State
from asaa import blood_time, blood_names
from tests.test_about import MemoryTray
from tests.test_icon_ui import MemoryIcons
from tests.test_wallpapers import MemoryBackend


class VeriNamesUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='asaa-veri-names-')
        root = Path(self.directory.name)
        self.environment = patch.dict(os.environ, {'XDG_DATA_HOME': str(root/'data')})
        self.environment.start()
        self.tray = patch('asaa.app.QSystemTrayIcon', MemoryTray)
        self.tray.start()
        self.state = State(root/'state.json')
        self.controller = Controller(self.app, self.state, network=False,
            wallpaper_backend=MemoryBackend(), icon_backend=MemoryIcons())
        self.controller.tick_timer.stop()
        self.now = datetime(2026, 10, 24, 15, 30, tzinfo=ZoneInfo('Europe/Helsinki'))
        self.controller.calendars.now = lambda: self.now
        self.window = self.controller.window
        self.app.processEvents()

    def tearDown(self):
        self.controller.shutdown()
        self.window.hide(); self.window.deleteLater()
        for widget in self.controller.widgets.values():
            widget.hide(); widget.deleteLater()
        self.controller.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete); self.app.processEvents()
        self.tray.stop(); self.environment.stop(); self.directory.cleanup()

    def test_birthday_lookup_before_epoch_names_the_cycle_without_writing_state(self):
        page = self.window.page_widgets['names']
        before = copy.deepcopy(self.state.data)
        saved = self.state.path.read_bytes() if self.state.path.exists() else None
        birthday = date(1985, 2, 14)
        page.set_day(birthday)
        pair = blood_names.names_for_day(birthday)
        self.assertIn(pair.male, page.name_labels['blood'].text())
        self.assertIn(pair.female, page.name_labels['blood'].text())
        self.assertIn('777 päivän nimikierto', page.position_labels['blood'].text())
        self.assertIn('ennen ajanlaskun alkua', page.position_labels['blood'].text())
        self.assertNotIn('vuosi 0000', page.position_labels['blood'].text())
        self.assertEqual(self.state.data, before)
        self.assertEqual(self.state.path.read_bytes() if self.state.path.exists() else None, saved)
        self.assertEqual(set(page.name_labels), {'shadow', 'star', 'blood', 'finnish'})

    def test_calendar_name_link_opens_the_same_selected_day(self):
        page = self.window.page_widgets['blood']
        selected = blood_time.EPOCH_DATE + timedelta(days=776)
        page.set_day(selected)
        names = page.selected_names.text()
        page.name_lookup.click()
        self.app.processEvents()
        target = self.window.page_widgets['names']
        self.assertTrue(self.window.navigation['names'].isChecked())
        self.assertEqual(target.tabs.currentIndex(), 0)
        self.assertEqual(target.date.date(), QDate(selected.year, selected.month, selected.day))
        self.assertEqual(target.name_labels['blood'].text(), names)
        self.assertIn('777/777', target.position_labels['blood'].text())
        target.set_day(selected + timedelta(days=1))
        self.assertIn('kohta 1/777', target.position_labels['blood'].text())
        self.assertIn('vuosi 0002', target.position_labels['blood'].text())

    def test_minimum_window_keeps_veri_calendar_within_the_viewport(self):
        self.window.resize(1020, 720)
        self.controller.open_page('blood')
        self.app.processEvents()
        page = self.window.page_widgets['blood']
        scroll = self.window.pages.currentWidget()
        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
        self.assertLessEqual(page.width(), self.window.pages.width())
        self.assertTrue(all(item.isVisible() for item in page.day_buttons))
        self.assertFalse(page.grab().isNull())
        self.controller.open_page('names')
        self.app.processEvents()
        scroll = self.window.pages.currentWidget()
        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)


if __name__ == '__main__':
    unittest.main()
