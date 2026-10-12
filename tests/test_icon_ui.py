"""Appearance controls exercise only temporary state and in-memory GNOME doubles."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from asaa.app import Controller
from asaa.icon_themes import INTERFACE, ICON_KEY, THEMES, validate_plan
from asaa.state import State
from asaa.wallpapers import DESKTOP, SAVER
from tests.test_wallpapers import MemoryBackend


class MemoryIcons:
    def __init__(self):
        self.ready=True
        self.values={ICON_KEY:'Yaru','gtk-theme':'Yaru','cursor-theme':'Yaru'}
        self.calls=[]
        self.fail=False
        self.default='Yaru-default'

    def desktop_available(self): return self.ready
    def read(self,schema,key): return self.values[key]
    def default_theme(self): return self.default
    def preflight(self,plan): validate_plan(plan)
    def write(self,schema,values):
        self.preflight({schema:values})
        self.calls.append(copy.deepcopy(values))
        if self.fail:
            self.fail=False
            raise OSError('simulated icon write failure')
        self.values.update(values)


class MemoryInstaller:
    def __init__(self): self.themes=[];self.repairs=[];self.restores=[];self.fail_restore=False
    def install_theme(self,source,destination): self.themes.append(source.name)
    def fix_app_launchers(self,data_home,all_apps=False):
        self.repairs.append(all_apps)
        return (3,[] if all_apps else ['Other app'])
    def restore_app_launchers(self,data_home):
        self.restores.append(data_home)
        if self.fail_restore: raise OSError('simulated launcher restore failure')
        return 3


class IconUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='asaa-icon-ui-')
        self.directory=Path(self.temporary.name)
        self.environment=patch.dict(os.environ,{'XDG_DATA_HOME':str(self.directory/'data')})
        self.environment.start()
        self.wallpapers=MemoryBackend()
        self.icons=MemoryIcons()
        self.state=State(self.directory/'state.json')
        self.controller=Controller(self.app,self.state,network=False,
            wallpaper_backend=self.wallpapers,icon_backend=self.icons)
        self.installer=MemoryInstaller()
        self.controller.icon_themes.installer=self.installer
        self.controller.tick_timer.stop()
        self.settings=self.controller.window.page_widgets['settings']
        self.gallery=self.controller.window.page_widgets['wallpapers']
        self.app.processEvents()

    def tearDown(self):
        self.controller.shutdown()
        self.controller.window.hide()
        self.controller.window.deleteLater()
        for widget in self.controller.widgets.values(): widget.hide();widget.deleteLater()
        self.controller.deleteLater()
        # The unit suite runs before QApplication.exec(). Drain deferred deletes
        # so later global font/style checks do not repaint retired test windows.
        self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.environment.stop()
        self.temporary.cleanup()

    @staticmethod
    def choose(control,value): control.setCurrentIndex(control.findData(value))

    def test_default_opening_and_policy_drafts_leave_desktop_unchanged(self):
        before=copy.deepcopy(self.state.data)
        self.assertFalse(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertFalse(self.gallery.theme_options.icon_behavior.currentData())
        for page in ('settings','wallpapers'):
            self.controller.open_page(page);self.app.processEvents()
        self.choose(self.gallery.theme_options.icon_behavior,True)
        self.choose(self.gallery.theme_options.behavior,False)
        self.controller.settings_changed.emit();self.app.processEvents()
        self.controller.open_page('settings');self.controller.open_page('wallpapers')
        self.app.processEvents()
        self.assertTrue(self.gallery.theme_options.icon_behavior.currentData())
        self.assertFalse(self.gallery.theme_options.behavior.currentData())
        self.assertEqual(self.state.data,before)
        self.assertEqual(self.icons.calls,[])
        self.assertEqual(self.wallpapers.calls,[])
        self.assertEqual(self.installer.themes,[])
        self.assertEqual(self.installer.repairs,[])

    def test_saved_policies_sync_both_pages_without_losing_other_drafts(self):
        self.choose(self.settings.wallpaper_options.target,'both')
        self.choose(self.gallery.theme_options.behavior,False)
        self.choose(self.gallery.theme_options.icon_behavior,True)
        self.gallery.save_theme_policy();self.app.processEvents()
        self.assertTrue(self.state.settings['icon_follow_theme'])
        self.assertTrue(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertFalse(self.settings.wallpaper_options.behavior.currentData())
        self.assertEqual(self.settings.wallpaper_options.target.currentData(),'both')
        self.choose(self.settings.wallpaper_options.icon_behavior,False)
        self.choose(self.gallery.theme_options.behavior,True)
        self.gallery.save_theme_policy();self.app.processEvents()
        self.assertFalse(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertTrue(self.settings.wallpaper_options.behavior.currentData())
        self.settings.save();self.app.processEvents()
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.assertFalse(self.gallery.theme_options.icon_behavior.currentData())
        self.assertEqual(self.gallery.theme_options.target.currentData(),'both')
        self.assertFalse(State(self.state.path).settings['icon_follow_theme'])
        self.assertEqual(self.icons.calls,[])
        self.assertEqual(self.wallpapers.calls,[])
        self.assertEqual(self.installer.themes,[])

    def test_explicit_icon_actions_use_saved_theme_and_do_not_save_drafts(self):
        self.controller.configure({'theme':'frost','wallpaper_follow_theme':False})
        self.wallpapers.calls.clear()
        self.choose(self.settings.theme,'ubuntu')
        self.choose(self.settings.wallpaper_options.icon_behavior,True)
        self.choose(self.settings.wallpaper_options.behavior,True)
        saved=copy.deepcopy(self.state.data)
        self.controller.open_page('settings');self.app.processEvents()
        QTest.mouseClick(self.settings.icon_actions.apply_button,Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],THEMES['frost'])
        self.assertIn('Halla',self.settings.icon_actions.status.text())
        self.assertEqual(self.state.data,saved)
        self.assertTrue(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertEqual(self.settings.theme.currentData(),'ubuntu')
        self.assertEqual(self.icons.values['gtk-theme'],'Yaru')
        self.assertEqual(self.icons.values['cursor-theme'],'Yaru')
        self.assertEqual(self.wallpapers.calls,[])
        QTest.mouseClick(self.settings.icon_actions.install_button,Qt.MouseButton.LeftButton)
        self.settings.icon_actions.all_apps.setChecked(True)
        QTest.mouseClick(self.settings.icon_actions.install_button,Qt.MouseButton.LeftButton)
        self.assertEqual(self.installer.repairs,[False,True])
        self.assertEqual(self.state.data,saved)
        self.assertEqual(self.icons.values[ICON_KEY],THEMES['frost'])

    def test_restore_disables_saved_follow_policy_while_preserving_draft(self):
        self.controller.configure({'wallpaper_follow_theme':False,'icon_follow_theme':True})
        self.gallery.icon_actions.apply_current_theme()
        self.gallery.icon_actions.restore_theme();self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],'Yaru')
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.assertFalse(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertFalse(self.gallery.theme_options.icon_behavior.currentData())
        self.choose(self.gallery.theme_options.icon_behavior,True)
        self.gallery.icon_actions.restore_theme();self.app.processEvents()
        self.assertTrue(self.gallery.theme_options.icon_behavior.currentData())
        self.assertFalse(self.state.settings['icon_follow_theme'])

    def test_missing_gnome_disables_activation_but_allows_explicit_install(self):
        self.icons.ready=False
        self.controller.settings_changed.emit();self.app.processEvents()
        for controls in (self.settings.wallpaper_options,self.gallery.theme_options):
            self.assertFalse(controls.icon_behavior.model().item(controls.icon_behavior.findData(True)).isEnabled())
            self.assertIn('GNOME',controls.icon_support.text())
        self.assertFalse(self.settings.icon_actions.apply_button.isEnabled())
        self.assertFalse(self.settings.icon_actions.default_button.isEnabled())
        self.assertTrue(self.settings.icon_actions.install_button.isEnabled())
        self.settings.icon_actions.install_button.click()
        self.assertEqual(self.installer.repairs,[False])
        self.assertEqual(self.icons.calls,[])

    def test_icon_write_error_is_reported_and_preserves_saved_state(self):
        before=copy.deepcopy(self.state.data)
        self.icons.fail=True
        self.gallery.icon_actions.apply_current_theme()
        self.assertIn('simulated icon write failure',self.gallery.icon_actions.status.text())
        self.assertEqual(self.state.data,before)
        self.assertEqual(self.icons.values[ICON_KEY],'Yaru')

    def test_system_default_button_needs_no_backup_and_preserves_other_drafts(self):
        self.icons.values[ICON_KEY]='Papirus'
        self.controller.configure({'icon_follow_theme':True})
        self.assertFalse(self.controller.icon_themes.backup.exists())
        for actions in (self.settings.icon_actions,self.gallery.icon_actions):
            self.assertTrue(actions.default_button.isEnabled())
            self.assertFalse(actions.restore_button.isEnabled())
        before=copy.deepcopy(self.state.data)
        before['settings']['icon_follow_theme']=False
        self.choose(self.settings.theme,'frost')
        self.choose(self.settings.wallpaper_options.target,'both')
        self.choose(self.gallery.theme_options.behavior,False)
        self.controller.open_page('settings');self.app.processEvents()
        QTest.mouseClick(self.settings.icon_actions.default_button,Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],'Yaru-default')
        self.assertEqual(State(self.state.path).data,before)
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.assertEqual(self.settings.theme.currentData(),'frost')
        self.assertEqual(self.settings.wallpaper_options.target.currentData(),'both')
        self.assertFalse(self.gallery.theme_options.behavior.currentData())
        self.assertFalse(self.settings.wallpaper_options.icon_behavior.currentData())
        self.assertFalse(self.gallery.theme_options.icon_behavior.currentData())
        self.assertEqual(self.installer.restores,[])
        self.assertEqual(self.wallpapers.calls,[])
        self.assertIn('Yaru-default',self.settings.icon_actions.status.text())
        for actions in (self.settings.icon_actions,self.gallery.icon_actions):
            self.assertEqual(actions.current.text(),'Käytössä: Yaru-default')

    def test_system_default_is_distinct_from_previous_and_restores_launchers(self):
        self.icons.values[ICON_KEY]='Papirus'
        self.gallery.icon_actions.apply_current_theme()
        self.controller.configure({'icon_follow_theme':True})
        backup=self.controller.icon_themes.backup.read_bytes()
        registry=self.controller.icon_themes.data_home/'ajanlaskut-icon-themes/launchers.json'
        registry.parent.mkdir(parents=True)
        registry.write_text('{"example.desktop": {}}')
        self.gallery.icon_actions.use_system_default();self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],'Yaru-default')
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.assertEqual(self.installer.restores,[self.controller.icon_themes.data_home])
        self.assertEqual(self.controller.icon_themes.backup.read_bytes(),backup)
        self.assertTrue(self.gallery.icon_actions.restore_button.isEnabled())
        self.gallery.icon_actions.restore_theme();self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],'Papirus')

    def test_default_launcher_restore_failure_reports_committed_default_and_refreshes(self):
        self.controller.configure({'icon_follow_theme':True})
        registry=self.controller.icon_themes.data_home/'ajanlaskut-icon-themes/launchers.json'
        registry.parent.mkdir(parents=True)
        registry.write_text('{"example.desktop": {}}')
        self.installer.fail_restore=True
        self.gallery.icon_actions.use_system_default();self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],'Yaru-default')
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.assertIn('sovelluskuvakkeiden palautus epäonnistui',self.gallery.icon_actions.status.text())
        self.assertIn('simulated launcher restore failure',self.gallery.icon_actions.status.text())
        for actions in (self.settings.icon_actions,self.gallery.icon_actions):
            self.assertEqual(actions.current.text(),'Käytössä: Yaru-default')
        self.assertEqual(self.wallpapers.calls,[])

    def test_new_dark_theme_is_a_draft_until_saved_and_icons_are_optional(self):
        choice=self.settings.theme.findData('ubuntu2610_dark')
        self.assertGreaterEqual(choice,0)
        self.assertEqual(self.settings.theme.itemText(choice),'Ubuntu 26.10 Dark')
        before=copy.deepcopy(self.state.data)
        self.choose(self.settings.theme,'ubuntu2610_dark')
        self.app.processEvents()
        self.assertEqual(self.state.data,before)
        self.assertEqual(self.icons.calls,[])
        self.assertEqual(self.wallpapers.calls,[])
        self.choose(self.settings.wallpaper_options.behavior,False)
        self.settings.save();self.app.processEvents()
        self.assertEqual(State(self.state.path).settings['theme'],'ubuntu2610_dark')
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.assertEqual(self.icons.calls,[])
        self.assertEqual(self.installer.themes,[])
        self.assertEqual(self.gallery.current_theme_button.text(),'Aseta Ubuntu 26.10 Dark-teeman tausta')
        self.assertEqual(self.controller.window.theme_title.text(),'UBUNTU 26.10 DARK')

    def test_dark_theme_manual_icons_and_wallpaper_work_without_follow_policy(self):
        self.controller.configure({'theme':'ubuntu2610_dark','wallpaper_follow_theme':False})
        before=copy.deepcopy(self.state.data)
        lock=copy.deepcopy(self.wallpapers.values[SAVER])
        self.gallery.icon_actions.apply_current_theme();self.app.processEvents()
        self.assertEqual(self.icons.values[ICON_KEY],THEMES['ubuntu2610_dark'])
        self.assertEqual(self.gallery.icon_actions.current.text(),'Käytössä: Ubuntu 26.10 Dark')
        self.assertEqual(self.settings.icon_actions.current.text(),'Käytössä: Ubuntu 26.10 Dark')
        self.assertEqual(self.installer.themes,['Ajanlaskut-Ubuntu-2610-Dark'])
        self.assertIn('Ubuntu 26.10 Dark',self.gallery.icon_actions.status.text())
        self.gallery.apply_current_theme();self.app.processEvents()
        picture=self.controller.wallpapers.library.for_theme('ubuntu2610_dark')
        self.assertEqual(picture.theme,'ubuntu2610_dark')
        expected=self.controller.wallpapers.library.preserve(picture.path).as_uri()
        self.assertEqual(self.wallpapers.values[DESKTOP]['picture-uri'],expected)
        self.assertEqual(self.wallpapers.values[SAVER],lock)
        self.assertEqual(self.state.data,before)
        self.gallery.icon_actions.install()
        self.assertEqual(set(self.installer.themes),set(THEMES.values()))

    def test_controls_fit_existing_minimum_window_width(self):
        self.controller.configure({'theme':'ubuntu2610_dark','wallpaper_follow_theme':False})
        for size in ((1020,720),(1280,860)):
            self.controller.window.resize(*size)
            for key in ('settings','wallpapers'):
                self.controller.open_page(key);self.app.processEvents()
                scroll=self.controller.window.pages.currentWidget()
                page=self.controller.window.page_widgets[key]
                self.assertLessEqual(page.width(),scroll.viewport().width(),(key,size))
                self.assertEqual(scroll.horizontalScrollBar().maximum(),0,(key,size))


if __name__=='__main__': unittest.main()
