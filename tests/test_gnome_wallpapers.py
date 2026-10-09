"""Real GI/schema APIs, but GSETTINGS_BACKEND=memory in a separate process."""
import importlib.util
import os
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec('gi'), 'Optional python3-gi is not installed')
class GioWallpaperTests(unittest.TestCase):
    def test_real_gio_write_and_readback_never_uses_user_dconf(self):
        source = '''
from asaa.wallpapers import GioBackend, DESKTOP, DIA
backend = GioBackend()
if not backend.desktop_available():
    raise SystemExit(77)
plan = {DESKTOP: {'picture-uri': 'file:///isolated-test.png',
    'picture-uri-dark': 'file:///isolated-test.png', 'picture-options': 'zoom'}}
backend.preflight(plan)
backend.write(DESKTOP, plan[DESKTOP])
assert backend.read(DESKTOP, 'picture-uri-dark') == 'file:///isolated-test.png'
try:
    backend.object(DIA)
except ValueError:
    pass
else:
    values = {'lock-mode': 'slideshow', 'lock-interval': 77, 'lock-shuffle': True,
        'lock-files': ['file:///one.png', 'file:///two.png']}
    backend.preflight({DIA: values})
    backend.write(DIA, values)
    assert backend.read(DIA, 'lock-files') == values['lock-files']
    assert backend.read(DIA, 'lock-interval') == 77
# Active-extension detection is a read-only D-Bus call and must not crash.
assert isinstance(backend.dia_active(), bool)
print('PASS: real Gio type conversion, delay/apply and readback using memory only')
'''
        environment = {**os.environ, 'GSETTINGS_BACKEND': 'memory'}
        result = subprocess.run([sys.executable, '-c', source], env=environment,
                                capture_output=True, text=True, timeout=15)
        if result.returncode == 77: self.skipTest('GNOME schemas are not installed')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS:', result.stdout)
