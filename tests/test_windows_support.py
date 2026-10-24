"""Windows adapters and their failure paths; no real registry writes."""
from contextlib import nullcontext
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from asaa import platform_support as platform
from asaa import startup
from asaa.calendar import Calendars
from asaa.state import State


class WindowsSupportTests(unittest.TestCase):
    def test_windows_storage_uses_local_appdata_even_when_xdg_is_present(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(platform, 'IS_WINDOWS', True), \
                patch.dict(os.environ, {'LOCALAPPDATA': folder, 'XDG_DATA_HOME': folder + '/wrong'}):
            self.assertEqual(platform.app_data_directory(), Path(folder) / 'AjanlaskutJaSaa')
            self.assertEqual(platform.weather_cache_directory(), Path(folder) / 'AjanlaskutJaSaa/cache/weather')

    def test_all_windows_theme_selections_persist_for_shared_and_individual_widgets(self):
        with tempfile.TemporaryDirectory() as folder:
            for theme in platform.WINDOWS_THEMES:
                state = State(Path(folder) / 'state.json')
                state.configure({'theme': theme, 'time_theme': theme,
                                 'widget_themes': {'combined': theme, 'weather': theme}})
                self.assertEqual(State(state.path).settings, state.settings)

    def test_windows_autostart_sets_only_own_hkcu_value_and_removes_it(self):
        registry = SimpleNamespace(HKEY_CURRENT_USER=object(), REG_SZ=1,
            CreateKey=Mock(side_effect=lambda *args: nullcontext('key')),
            SetValueEx=Mock(), DeleteValue=Mock())
        with patch.dict(sys.modules, winreg=registry), patch.object(startup, 'IS_WINDOWS', True), \
                patch.object(startup, 'windows_command', return_value='"C:\\Oma kansio\\kello.exe" --widgets-only'):
            startup.set_autostart(True); startup.set_autostart(False)
            registry.SetValueEx.assert_called_once_with('key', 'AjanlaskutJaSaa', 0, 1,
                                                       '"C:\\Oma kansio\\kello.exe" --widgets-only')
            registry.DeleteValue.assert_called_once_with('key', 'AjanlaskutJaSaa')
            self.assertIs(registry.CreateKey.call_args.args[0], registry.HKEY_CURRENT_USER)

    def test_disabling_missing_autostart_is_idempotent(self):
        registry = SimpleNamespace(HKEY_CURRENT_USER=object(),
            CreateKey=Mock(return_value=nullcontext('key')), DeleteValue=Mock(side_effect=FileNotFoundError))
        with patch.dict(sys.modules, winreg=registry), patch.object(startup, 'IS_WINDOWS', True):
            startup.set_autostart(False)

    def test_windows_command_quotes_paths_with_spaces_and_unicode(self):
        with tempfile.TemporaryDirectory(prefix='aika ä ') as folder:
            module = Path(folder) / 'asaa/platform_support.py'
            executable = Path(folder) / 'Ajanlaskut-ja-Saa.exe'; executable.touch()
            with patch.object(platform, '__file__', str(module)):
                self.assertEqual(platform.windows_command(True),
                                 subprocess.list2cmdline([str(executable.resolve()), '--widgets-only']))

    def test_time_configuration_is_read_without_claiming_a_live_sync(self):
        registry = SimpleNamespace(HKEY_LOCAL_MACHINE=object(),
            OpenKey=Mock(return_value=nullcontext('key')),
            QueryValueEx=Mock(return_value=('time.mikes.fi,0x9', 1)))
        with patch.dict(sys.modules, winreg=registry):
            self.assertEqual(platform.windows_time_server(), 'time.mikes.fi,0x9')
            registry.QueryValueEx.assert_called_once_with('key', 'NtpServer')

    def test_clock_reads_system_instant_with_helsinki_dst(self):
        clock = Calendars()
        before = datetime.now(timezone.utc)
        now = clock.now()
        after = datetime.now(timezone.utc)
        self.assertLessEqual(before, now); self.assertLessEqual(now, after)
        from zoneinfo import ZoneInfo
        zone = ZoneInfo('Europe/Helsinki')
        self.assertEqual(datetime(2026, 1, 15, tzinfo=zone).utcoffset().total_seconds(), 7200)
        self.assertEqual(datetime(2026, 7, 15, tzinfo=zone).utcoffset().total_seconds(), 10800)

    def test_windows_byte_lock_unlocks_even_on_exception(self):
        locks = SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2, locking=Mock())
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, msvcrt=locks), \
                patch.object(platform, 'IS_WINDOWS', True):
            with self.assertRaisesRegex(ValueError, 'test'):
                with platform.locked_file(Path(folder) / 'weather.lock'):
                    raise ValueError('test')
            self.assertEqual([call.args[1:] for call in locks.locking.call_args_list], [(1, 1), (2, 1)])

    def test_cache_lock_serializes_real_processes_and_releases(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'weather.lock'
            command = ('from asaa.platform_support import locked_file; from pathlib import Path; '
                       'print("ready",flush=True); '
                       f'\nwith locked_file(Path({str(path)!r})): print("acquired",flush=True)')
            process = None
            try:
                with platform.locked_file(path):
                    process = subprocess.Popen([sys.executable, '-c', command], stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, text=True)
                    self.assertEqual(process.stdout.readline().strip(), 'ready')
                    with self.assertRaises(subprocess.TimeoutExpired): process.communicate(timeout=.25)
                output, error = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, error); self.assertIn('acquired', output)
            finally:
                if process and process.poll() is None: process.kill(); process.communicate()

    def test_contended_windows_lock_times_out_without_unlocking_another_owner(self):
        for code in (0, 13):
            locks = SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2, locking=Mock(side_effect=OSError(code, 'busy')))
            with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, msvcrt=locks), \
                    patch.object(platform, 'IS_WINDOWS', True):
                with self.assertRaises(TimeoutError):
                    with platform.locked_file(Path(folder) / 'weather.lock', timeout=0): pass
                self.assertEqual([call.args[1] for call in locks.locking.call_args_list], [1])

    def test_windows_light_dark_and_high_contrast_colors(self):
        from asaa import windows_appearance as appearance
        with patch.object(appearance, 'high_contrast', return_value=False), \
                patch.object(appearance, 'apps_are_dark', return_value=True):
            self.assertEqual(appearance.windows_colors('windows_system')['background'], '#202020')
            self.assertEqual(appearance.windows_colors('windows_light')['background'], '#ffffff')
        with patch.object(appearance, 'high_contrast', return_value=True), \
                patch.object(appearance, 'system_color', side_effect=lambda index: f'#{index:06x}'):
            for theme in platform.WINDOWS_THEMES:
                colors = appearance.windows_colors(theme)
                self.assertEqual(colors['text'], '#000008')
                self.assertEqual(colors['muted'], colors['text'])


if __name__ == '__main__': unittest.main()
