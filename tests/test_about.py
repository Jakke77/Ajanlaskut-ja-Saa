"""About actions identify the running installation without saving appearance drafts."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QEvent, QTimer, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QSystemTrayIcon

import asaa
from asaa.about import AboutDialog
from asaa.app import Controller, ROOT, VERSION
from asaa.state import State
from tests.test_icon_ui import MemoryIcons, MemoryInstaller
from tests.test_wallpapers import MemoryBackend


class MemoryTray:
    ActivationReason=QSystemTrayIcon.ActivationReason

    @staticmethod
    def isSystemTrayAvailable(): return True
    def __init__(self,*args): self.activated=Mock();self.menu=None
    def setToolTip(self,value): pass
    def setContextMenu(self,menu): self.menu=menu
    def show(self): pass
    def hide(self): pass


class AboutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='asaa-about-')
        self.directory=Path(self.temporary.name)
        self.environment=patch.dict(os.environ,{'XDG_DATA_HOME':str(self.directory/'data')})
        self.environment.start()
        self.tray_patch=patch('asaa.app.QSystemTrayIcon',MemoryTray);self.tray_patch.start()
        self.icons=MemoryIcons();self.wallpapers=MemoryBackend()
        self.state=State(self.directory/'state.json')
        self.controller=Controller(self.app,self.state,network=False,
            wallpaper_backend=self.wallpapers,icon_backend=self.icons)
        self.installer=MemoryInstaller();self.controller.icon_themes.installer=self.installer
        self.controller.tick_timer.stop()
        self.settings=self.controller.window.page_widgets['settings']
        self.app.processEvents()

    def tearDown(self):
        self.controller.shutdown();self.controller.window.hide();self.controller.window.deleteLater()
        for widget in self.controller.widgets.values():widget.hide();widget.deleteLater()
        self.controller.deleteLater()
        self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents()
        self.tray_patch.stop();self.environment.stop();self.temporary.cleanup()

    def open_and_close(self,action):
        observed=[]
        def close():
            dialog=self.app.activeModalWidget()
            if isinstance(dialog,AboutDialog):
                observed.append((dialog.name.text(),dialog.version.text(),dialog.installation.text()))
                observed.append((dialog.installation.isReadOnly(),dialog.isModal(),dialog.project.text()))
                QTest.mouseClick(dialog.findChild(QDialogButtonBox).button(
                    QDialogButtonBox.StandardButton.Close),Qt.MouseButton.LeftButton)
            elif dialog is not None:dialog.reject()
        QTimer.singleShot(0,close)
        action()
        self.assertEqual(observed[0],('Ajanlaskut ja Sää','Versio '+VERSION,str(ROOT)))
        self.assertEqual(observed[1][:2],(True,True))
        self.assertIn('https://github.com/Jakke77/Ajanlaskut-ja-Saa',observed[1][2])
        self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents()

    def test_help_and_settings_open_about_without_saving_drafts(self):
        self.controller.open_page('settings');self.controller.window.resize(1020,720)
        self.app.processEvents()
        self.settings.theme.setCurrentIndex(self.settings.theme.findData('frost'))
        self.settings.wallpaper_options.icon_behavior.setCurrentIndex(
            self.settings.wallpaper_options.icon_behavior.findData(True))
        before=copy.deepcopy(self.state.data)
        saved=self.state.path.read_bytes() if self.state.path.exists() else None
        self.assertEqual(self.controller.window.help_menu.title(),'Ohje')
        self.assertEqual(self.controller.window.about_action.text(),'Tietoa sovelluksesta')
        self.open_and_close(self.controller.window.about_action.trigger)
        scroll=self.controller.window.pages.currentWidget()
        scroll.ensureWidgetVisible(self.settings.about_button);self.app.processEvents()
        self.assertTrue(self.settings.about_button.isVisible())
        self.assertEqual(self.settings.about_button.text(),'Tietoa sovelluksesta')
        self.open_and_close(lambda:QTest.mouseClick(self.settings.about_button,Qt.MouseButton.LeftButton))
        self.assertEqual(self.state.data,before)
        self.assertEqual(self.state.path.read_bytes() if self.state.path.exists() else None,saved)
        self.assertEqual(self.settings.theme.currentData(),'frost')
        self.assertTrue(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertEqual(self.icons.calls,[]);self.assertEqual(self.wallpapers.calls,[])
        self.assertEqual(self.installer.themes,[]);self.assertEqual(self.installer.repairs,[])

    def test_weather_and_tray_identify_the_same_running_installation(self):
        menus=(self.controller.weather.make_menu(),self.controller.tray.menu)
        for menu in menus:
            matches=[action for action in menu.actions() if action.text()=='Tietoa sovelluksesta']
            self.assertEqual(len(matches),1)
            self.open_and_close(matches[0].trigger)
        self.assertEqual(self.icons.calls,[]);self.assertEqual(self.wallpapers.calls,[])

    def test_loaded_version_does_not_change_when_module_metadata_changes(self):
        # An upgrade may replace files while an older process is still running.
        # The dialog must identify this process rather than reread those files.
        with patch.object(asaa,'VERSION','99.0.0'):
            self.open_and_close(self.controller.show_about)


if __name__=='__main__':unittest.main()
