"""Hermetic icon-theme and combined appearance transaction checks."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from PyQt6.QtGui import QColor, QImage

from asaa.icon_themes import IconThemeManager, INTERFACE, ICON_KEY, THEMES, validate_plan
from asaa.state import State, atomic_json
from asaa.wallpapers import WallpaperManager
from tests.test_wallpapers import MemoryBackend


class MemoryIconBackend:
    """Injectable desktop state; failure deliberately happens after a write."""
    def __init__(self, available=True):
        self.desktop = available
        self.values = {INTERFACE: {ICON_KEY: 'Yaru', 'gtk-theme': 'Yaru-dark', 'color-scheme': 'prefer-dark'}}
        self.calls = []
        self.fail = False

    def desktop_available(self): return self.desktop
    def read(self, schema, key): return self.values[schema][key]
    def preflight(self, plan): validate_plan(plan)
    def write(self, schema, values):
        validate_plan({schema: values})
        self.calls.append((schema, copy.deepcopy(values)))
        self.values[schema].update(values)
        if self.fail:
            self.fail = False
            raise OSError('simulated icon storage failure')


class MemoryInstaller:
    """No subprocesses or scans of host launchers."""
    def __init__(self):
        self.installed = []
        self.launcher_calls = []
        self.restore_calls = []
        self.fail = False

    def install_theme(self, source, destination):
        if self.fail: raise OSError('simulated installation failure')
        self.installed.append((source, destination))
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def fix_app_launchers(self, data_home, all_apps=False):
        self.launcher_calls.append((data_home, all_apps))
        return 3, ([] if all_apps else ['unknown.desktop'])

    def restore_app_launchers(self, data_home):
        self.restore_calls.append(data_home)


class IconThemeFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ajanlaskut-icons-test-')
        self.root = Path(self.temporary.name)
        self.bundle = self.root / 'bundle'
        for name in THEMES.values():
            directory = self.bundle / name
            directory.mkdir(parents=True)
            (directory / 'index.theme').write_text('[Icon Theme]\nName=' + name + '\n')
        self.backend = MemoryIconBackend()
        self.installer = MemoryInstaller()
        self.manager = IconThemeManager(self.bundle, self.root / 'data', self.backend,
            data_home=self.root / 'xdg', installer=self.installer)
        self.before = copy.deepcopy(self.backend.values)

    def tearDown(self): self.temporary.cleanup()


class IconThemeTests(IconThemeFixture, unittest.TestCase):
    def test_startup_and_status_are_read_only(self):
        self.assertTrue(self.manager.available())
        self.assertEqual(self.manager.current(), 'Yaru')
        self.assertFalse(self.manager.launcher_backup_exists())
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.installer.installed, [])
        self.assertFalse(self.manager.backup.exists())

    def test_apply_changes_only_icon_theme_and_never_fixes_launchers(self):
        self.manager.apply('frost')
        expected = copy.deepcopy(self.before)
        expected[INTERFACE][ICON_KEY] = THEMES['frost']
        self.assertEqual(self.backend.values, expected)
        self.assertEqual(len(self.installer.installed), 1)
        self.assertEqual(self.installer.installed[0][1], self.root / 'xdg/icons' / THEMES['frost'])
        self.assertEqual(self.installer.launcher_calls, [])

    def test_original_theme_survives_multiple_shared_theme_changes_and_reopen(self):
        self.manager.apply('copper'); self.manager.apply('frost')
        reopened = IconThemeManager(self.bundle, self.root / 'data', self.backend,
            data_home=self.root / 'xdg', installer=self.installer)
        reopened.apply('ubuntu')
        self.assertEqual(json.loads(self.manager.backup.read_text())['settings'], {INTERFACE: {ICON_KEY: 'Yaru'}})
        reopened.restore()
        self.assertEqual(self.backend.values, self.before)
        self.assertFalse(self.manager.backup.exists())

    def test_partial_backend_failure_rolls_back_and_skips_application_commit(self):
        commit = Mock(); self.backend.fail = True
        with self.assertRaisesRegex(OSError, 'icon storage failure'): self.manager.apply('copper', commit=commit)
        self.assertEqual(self.backend.values, self.before)
        self.assertFalse(self.manager.backup.exists())
        commit.assert_not_called()

    def test_failed_first_use_does_not_preserve_a_stale_original_theme(self):
        for failure in ('backend', 'settings'):
            with self.subTest(failure=failure):
                self.backend.values[INTERFACE][ICON_KEY] = 'Yaru'
                if failure == 'backend': self.backend.fail = True
                commit = Mock(side_effect=OSError('disk full')) if failure == 'settings' else None
                with self.assertRaises(OSError): self.manager.apply('copper', commit=commit)
                self.assertFalse(self.manager.backup.exists())
                self.backend.values[INTERFACE][ICON_KEY] = 'Papirus'
                self.manager.apply('frost'); self.manager.restore()
                self.assertEqual(self.manager.current(), 'Papirus')

    def test_failed_first_use_recovery_retains_its_undo_snapshot(self):
        original_write = self.backend.write
        self.backend.fail = True
        def write(schema, values):
            if values[ICON_KEY] == 'Yaru': raise OSError('recovery unavailable')
            original_write(schema, values)
        with patch.object(self.backend, 'write', side_effect=write):
            with self.assertRaisesRegex(OSError, 'palautus epäonnistui'):
                self.manager.apply('frost')
        self.assertEqual(json.loads(self.manager.backup.read_text())['settings'], {INTERFACE: {ICON_KEY: 'Yaru'}})
        self.manager.restore()
        self.assertEqual(self.manager.current(), 'Yaru')

    def test_failed_settings_commit_restores_current_theme_without_losing_original(self):
        self.manager.apply('copper')
        copper = copy.deepcopy(self.backend.values)
        commit = Mock(side_effect=OSError('disk full'))
        with self.assertRaisesRegex(OSError, 'disk full'): self.manager.apply('frost', commit=commit)
        self.assertEqual(self.backend.values, copper)
        self.manager.restore()
        self.assertEqual(self.backend.values, self.before)

    def test_original_backup_is_durable_before_any_desktop_write(self):
        with patch('asaa.icon_themes.atomic_json', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.manager.apply('copper')
        self.assertEqual(self.backend.calls, [])

    def test_failed_installation_leaves_desktop_and_settings_alone(self):
        self.installer.fail = True
        commit = Mock()
        with self.assertRaises(OSError): self.manager.apply('copper', commit=commit)
        commit.assert_not_called()
        self.assertEqual(self.backend.values, self.before)
        self.assertFalse(self.manager.backup.exists())

    def test_invalid_or_missing_theme_does_not_write_or_install(self):
        for theme in ('../other', 'Yaru', '', None):
            with self.assertRaises(ValueError): self.manager.apply(theme)
        (self.bundle / THEMES['copper'] / 'index.theme').unlink()
        with self.assertRaises(ValueError): self.manager.apply('copper')
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.installer.installed, [])

    def test_unavailable_desktop_still_supports_explicit_local_installation(self):
        self.backend.desktop = False
        with self.assertRaises(ValueError): self.manager.apply('copper')
        self.assertEqual(self.installer.installed, [])
        self.assertEqual(self.manager.install(), (3, ['unknown.desktop']))
        self.assertEqual(len(self.installer.installed), 3)
        self.assertEqual(self.installer.launcher_calls, [(self.root / 'xdg', False)])
        self.assertEqual(self.backend.calls, [])
        self.assertFalse(self.manager.backup.exists())

    def test_explicit_all_app_install_and_launcher_restore_do_not_activate(self):
        self.assertEqual(self.manager.install(all_apps=True), (3, []))
        self.manager.restore_launchers()
        self.assertEqual(self.installer.launcher_calls, [(self.root / 'xdg', True)])
        self.assertEqual(self.installer.restore_calls, [self.root / 'xdg'])
        self.assertEqual(self.backend.calls, [])

    def test_restore_rejects_other_interface_keys_and_schemas(self):
        bad = [{INTERFACE: {'gtk-theme': 'other'}},
               {INTERFACE: {ICON_KEY: 'Yaru', 'color-scheme': 'default'}},
               {'org.gnome.desktop.screensaver': {'lock-enabled': False}},
               {INTERFACE: {ICON_KEY: '../other'}}, {}, []]
        for settings in bad:
            atomic_json(self.manager.backup, {'version': 1, 'settings': settings})
            with self.assertRaises(ValueError): self.manager.restore()
            with self.assertRaises(ValueError): self.manager.apply('copper')
        self.assertEqual(self.backend.calls, [])

    def test_restore_state_commit_failure_keeps_current_icons(self):
        self.manager.apply('frost'); current = copy.deepcopy(self.backend.values)
        backup = self.manager.backup.read_bytes()
        with self.assertRaises(OSError): self.manager.restore(commit=Mock(side_effect=OSError('disk full')))
        self.assertEqual(self.backend.values, current)
        self.assertEqual(self.manager.backup.read_bytes(), backup)

    def test_successful_restore_starts_a_new_original_theme_lifecycle(self):
        self.manager.apply('copper'); self.manager.restore()
        self.assertFalse(self.manager.backup.exists())
        self.backend.values[INTERFACE][ICON_KEY] = 'Papirus'
        self.manager.apply('frost'); self.manager.restore()
        self.assertEqual(self.manager.current(), 'Papirus')
        self.assertFalse(self.manager.backup.exists())

    def test_old_state_defaults_to_disabled_without_modifying_file(self):
        state = State(self.root / 'old-state.json')
        old = copy.deepcopy(state.data)
        old['settings'].pop('icon_follow_theme')
        old['geometry']['weather'] = [123, 456]
        old['notes']['2026-10-12'] = 'Oma merkintä'
        atomic_json(state.path, old); raw = state.path.read_bytes()
        loaded = State(state.path)
        self.assertFalse(loaded.settings['icon_follow_theme'])
        self.assertEqual(state.path.read_bytes(), raw)
        self.assertEqual(loaded.data['geometry'], old['geometry'])
        self.assertEqual(loaded.data['notes'], old['notes'])

    def test_follow_policy_accepts_only_booleans_and_persists(self):
        state = State(self.root / 'state.json')
        for value in (0, 1, 'true', None):
            with self.assertRaises(ValueError): state.configure({'icon_follow_theme': value})
        state.configure({'icon_follow_theme': True})
        self.assertTrue(State(state.path).settings['icon_follow_theme'])


class ControllerHarness:
    """Exercise the real Controller commands without opening Qt windows."""
    def __init__(self, state, icons, wallpapers):
        self.state, self.icon_themes, self.wallpapers = state, icons, wallpapers
        self.app = Mock(); self.time_rotation = Mock(); self.weather = Mock(); self.daily = Mock()
        self.settings_changed = Mock(); self.clock_changed = Mock()
        self.window = Mock()
        self.window.page_widgets = {'calendar': Mock(), 'weather': Mock()}

    @property
    def options(self): return self.state.settings


class AppearanceTransactionTests(IconThemeFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        from asaa.app import Controller
        self.Controller = Controller
        self.wallpaper_backend = MemoryBackend()
        wallpaper_bundle = self.root / 'wallpapers'; wallpaper_bundle.mkdir()
        records = []
        for theme, color in (('copper', '#ef986e'), ('frost', '#a3cfe9'), ('ubuntu', '#e95420')):
            filename = theme + '.png'
            image = QImage(32, 18, QImage.Format.Format_RGB32)
            image.fill(QColor(color)); self.assertTrue(image.save(str(wallpaper_bundle / filename)))
            records.append({'file': filename, 'theme': theme, 'title': theme})
        atomic_json(wallpaper_bundle / 'catalog.json', {'version': 1, 'wallpapers': records})
        wallpapers = WallpaperManager(wallpaper_bundle, self.root / 'data', self.wallpaper_backend)
        self.state = State(self.root / 'state.json')
        self.state.commit(self.state.data)
        self.controller = ControllerHarness(self.state, self.manager, wallpapers)
        self.paint = patch('asaa.app.apply_theme'); self.paint.start(); self.addCleanup(self.paint.stop)

    def configure(self, changes): self.Controller.configure(self.controller, changes)

    def test_only_deliberate_shared_theme_change_follows_icons(self):
        self.configure({'icon_follow_theme': True})
        self.configure({'theme': 'copper'})
        self.configure({'font': 'DejaVu Sans'})
        self.configure({'widget_themes': {'weather': 'frost'}})
        self.configure({'time_theme': 'ubuntu', 'time_system': 'star'})
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.installer.installed, [])
        self.configure({'theme': 'frost'})
        self.assertEqual(self.backend.values[INTERFACE][ICON_KEY], THEMES['frost'])
        self.assertEqual(self.installer.launcher_calls, [])
        self.assertTrue(State(self.state.path).settings['icon_follow_theme'])

    def test_disabled_policy_leaves_desktop_icons_when_widget_and_wallpaper_change(self):
        self.configure({'theme': 'frost'})
        self.assertEqual(self.backend.values, self.before)
        self.assertTrue(self.wallpaper_backend.calls)

    def test_settings_failure_restores_icons_wallpaper_and_original_settings(self):
        self.configure({'icon_follow_theme': True})
        previous = copy.deepcopy(self.state.data); raw = self.state.path.read_bytes()
        backgrounds = copy.deepcopy(self.wallpaper_backend.values)
        with patch.object(self.state, 'commit', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'): self.configure({'theme': 'frost'})
        self.assertEqual(self.state.data, previous); self.assertEqual(self.state.path.read_bytes(), raw)
        self.assertEqual(self.backend.values, self.before)
        self.assertEqual(self.wallpaper_backend.values, backgrounds)

    def test_icon_failure_restores_wallpaper_and_never_commits_settings(self):
        self.configure({'icon_follow_theme': True})
        previous = copy.deepcopy(self.state.data); backgrounds = copy.deepcopy(self.wallpaper_backend.values)
        self.backend.fail = True
        with self.assertRaisesRegex(OSError, 'icon storage failure'): self.configure({'theme': 'frost'})
        self.assertEqual(self.state.data, previous)
        self.assertEqual(self.backend.values, self.before)
        self.assertEqual(self.wallpaper_backend.values, backgrounds)

    def test_wallpaper_failure_never_applies_icons_or_commits_settings(self):
        from asaa.wallpapers import DESKTOP
        self.configure({'icon_follow_theme': True})
        previous = copy.deepcopy(self.state.data); backgrounds = copy.deepcopy(self.wallpaper_backend.values)
        self.wallpaper_backend.fail = DESKTOP
        with self.assertRaises(OSError): self.configure({'theme': 'frost'})
        self.assertEqual(self.state.data, previous)
        self.assertEqual(self.wallpaper_backend.values, backgrounds)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.installer.installed, [])

    def test_unavailable_icon_backend_does_not_partially_change_shared_theme(self):
        self.configure({'icon_follow_theme': True}); self.backend.desktop = False
        previous = copy.deepcopy(self.state.data); backgrounds = copy.deepcopy(self.wallpaper_backend.values)
        with self.assertRaises(ValueError): self.configure({'theme': 'frost'})
        self.assertEqual(self.state.data, previous)
        self.assertEqual(self.wallpaper_backend.values, backgrounds)

    def test_manual_apply_ignores_follow_policy_and_restore_disables_follow(self):
        self.Controller.set_icon_theme(self.controller)
        self.assertEqual(self.backend.values[INTERFACE][ICON_KEY], THEMES['copper'])
        self.assertFalse(self.state.settings['icon_follow_theme'])
        self.configure({'icon_follow_theme': True})
        self.Controller.restore_icon_theme(self.controller)
        self.assertEqual(self.backend.values, self.before)
        self.assertFalse(State(self.state.path).settings['icon_follow_theme'])

    def test_restore_storage_failure_keeps_follow_policy_and_icons(self):
        self.Controller.set_icon_theme(self.controller); self.configure({'icon_follow_theme': True})
        previous = copy.deepcopy(self.state.data); icons = copy.deepcopy(self.backend.values)
        with patch.object(self.state, 'commit', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.Controller.restore_icon_theme(self.controller)
        self.assertEqual(self.state.data, previous)
        self.assertEqual(self.backend.values, icons)


if __name__ == '__main__': unittest.main()
