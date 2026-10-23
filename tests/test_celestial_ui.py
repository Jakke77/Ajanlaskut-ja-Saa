"""Actual Qt pages/widgets: birthday lookup, lunar months and live worker state."""
import copy
from datetime import date, datetime
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QDate, QEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from asaa.app import Controller
from asaa.state import State
from asaa.astronomy import moon_at, solar_day, lunar_day, moon_on
from asaa.namedays import names_for_day
from asaa.widgets import DesktopSurface
from tests.test_about import MemoryTray
from tests.test_icon_ui import MemoryIcons
from tests.test_wallpapers import MemoryBackend


class CelestialUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='asaa-celestial-')
        self.directory=Path(self.temporary.name)
        self.environment=patch.dict(os.environ,{'XDG_DATA_HOME':str(self.directory/'data')});self.environment.start()
        self.tray=patch('asaa.app.QSystemTrayIcon',MemoryTray);self.tray.start()
        self.state=State(self.directory/'state.json')
        self.controller=Controller(self.app,self.state,network=False,
            wallpaper_backend=MemoryBackend(),icon_backend=MemoryIcons())
        self.controller.tick_timer.stop()
        self.now=datetime(2026,10,23,15,tzinfo=ZoneInfo('Europe/Helsinki'))
        self.controller.calendars.now=lambda:self.now
        self.window=self.controller.window
        self.app.processEvents()

    def tearDown(self):
        self.controller.shutdown();self.window.hide();self.window.deleteLater()
        for widget in self.controller.widgets.values():widget.hide();widget.deleteLater()
        self.controller.deleteLater()
        self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents()
        self.tray.stop();self.environment.stop();self.temporary.cleanup()

    def test_birthday_before_epochs_has_two_names_per_system_without_saving(self):
        page=self.window.page_widgets['names'];self.controller.open_page('names')
        before=copy.deepcopy(self.state.data)
        saved=self.state.path.read_bytes() if self.state.path.exists() else None
        birthday=date(1985,2,14);page.date.setDate(QDate(1985,2,14));self.app.processEvents()
        for system in ('shadow','star'):
            expected=names_for_day(system,birthday)
            self.assertIn(expected.male,page.name_labels[system].text())
            self.assertIn(expected.female,page.name_labels[system].text())
        self.assertIn('Miehen nimi:',page.name_labels['finnish'].text())
        self.assertEqual(self.state.data,before)
        self.assertEqual(self.state.path.read_bytes() if self.state.path.exists() else None,saved)

    def test_calendar_links_open_actual_finnish_lunar_month_and_names(self):
        calendar=self.window.page_widgets['calendar']
        calendar.set_day('star',date(2028,2,25));calendar.open_folk_calendar()
        page=self.window.page_widgets['names'];self.app.processEvents()
        self.assertEqual(page.tabs.currentIndex(),1)
        self.assertIn('1. Vaahtokuu',page.folk_heading.text())
        self.assertIn('13 kuukauden',page.folk_info.text())
        self.assertIn('sovelluksen',page.folk_rules.text().lower())
        cells=[w for w in page.findChildren(QPushButton) if '\n' in w.text() and w.text().split('\n')[0].isdigit()]
        self.assertEqual(len([w for w in cells if not w.isHidden()]),30)
        self.assertIn('Mies:',page.folk_names.text())
        page.step(1);self.assertIn('Maaliskuu',page.folk_heading.text())

    def test_real_worker_fills_selected_day_and_month_with_reference_times(self):
        page=self.window.page_widgets['sunmoon'];page.date.setDate(QDate(2026,10,23))
        self.controller.open_page('sunmoon')
        for _ in range(300):
            if page.table.rowCount()==31:break
            QTest.qWait(25)
        self.assertEqual(page.table.rowCount(),31,page.status.text())
        self.assertIn('08:36',page.sun_text.text());self.assertIn('17:27',page.sun_text.text())
        self.assertIn('16:47',page.moon_times.text());self.assertIn('04:09',page.moon_times.text())
        self.assertIn('Kasvava kuu',page.moon_text.text())
        self.assertIn('Europe/Helsinki',page.place_label.text())
        self.assertTrue(page.bar.data);self.assertTrue(page.disk.info)
        self.assertTrue(page.grab().width()>500)

    def test_late_results_cannot_overwrite_new_date_or_stopped_page(self):
        page=self.window.page_widgets['sunmoon'];self.controller.open_page('sunmoon')
        page.date.setDate(QDate(2026,10,23));old_key=page._key
        args=(date(2026,10,23),65.0701,25.5071,'Europe/Helsinki')
        data=(solar_day(*args),lunar_day(*args),moon_on(args[0]),[])
        page.date.setDate(QDate(2026,10,24))
        page.daily_received(old_key,data);self.assertEqual(page.sun_text.text(),'')
        page.stop();page.daily_received(page._key,data)
        self.assertEqual(page.sun_text.text(),'')
        self.assertTrue(all(not worker.isRunning() for worker in page._workers))

    def test_both_real_clock_widgets_show_same_moon_and_own_name_pair(self):
        widget=DesktopSurface(self.controller,'combined',preview=True)
        self.now=datetime(2026,10,19,16,58,tzinfo=ZoneInfo('Europe/Helsinki'))
        expected=moon_at(self.now).label
        for system in ('shadow','star'):
            widget.system_override=system;widget.grab()
            self.assertIn(expected,widget.accessibleName())
            self.assertIn(names_for_day(system,self.now.date()).male,widget.toolTip())
        widget.system_override=None
        widget.deleteLater()


if __name__=='__main__':unittest.main()
