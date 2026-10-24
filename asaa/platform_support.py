"""Small OS adapters shared by storage, launchers and the Windows UI."""
from contextlib import contextmanager
import errno
import os
from pathlib import Path
import subprocess
import sys
import time

IS_WINDOWS = sys.platform == 'win32'
WINDOWS_THEMES = ('windows_system', 'windows_light', 'windows_dark')


def app_data_directory():
    if IS_WINDOWS:
        return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local') / 'AjanlaskutJaSaa'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'ajanlaskut-ja-saa'


def weather_cache_directory():
    if IS_WINDOWS:
        return app_data_directory() / 'cache/weather'
    return Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'pollonkangas-saa'


@contextmanager
def locked_file(path, timeout=60):
    """Serialize cache requests across processes, including on Windows.

    Windows byte locks need an existing byte and a fixed seek position. The
    descriptor is always closed, including on timeouts and failed requests.
    """
    with Path(path).open('a+b') as stream:
        if IS_WINDOWS:
            import msvcrt
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b'\0'); stream.flush()
            deadline = time.monotonic() + timeout
            while True:
                stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    # Some Windows CRT compatibility runtimes report errno 0
                    # for a conflicting byte lock. They still need the retry.
                    if error.errno not in (0, errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        raise
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Säätietojen välimuisti on toisen prosessin käytössä.') from error
                    time.sleep(.05)
            try:
                yield stream
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield stream


def windows_command(widgets_only=False):
    """Quote with Windows command-line rules, without involving a shell."""
    root = Path(__file__).resolve().parents[1]
    launcher = root / 'Ajanlaskut-ja-Saa.exe'
    if launcher.is_file():
        arguments = [str(launcher)]
    else:
        executable = Path(sys.executable)
        windowed = executable.with_name('pythonw.exe')
        arguments = [str(windowed if windowed.is_file() else executable), str(root / 'main.py')]
    if widgets_only:
        arguments.append('--widgets-only')
    return subprocess.list2cmdline(arguments)


def windows_time_server():
    """Read configuration only; a configured peer does not prove a live sync."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SYSTEM\CurrentControlSet\Services\W32Time\Parameters') as key:
            return str(winreg.QueryValueEx(key, 'NtpServer')[0])
    except (ImportError, OSError):
        return 'Katso Windowsin Internet-aika-asetuksista'
