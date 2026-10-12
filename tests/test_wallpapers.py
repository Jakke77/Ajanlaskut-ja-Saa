"""Hermetic background tests. These never write the user's GNOME settings."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtGui import QImage, QColor

from asaa.state import State, atomic_json
from asaa.theme import THEMES
from asaa.wallpapers import (WallpaperManager, WallpaperLibrary, image_size,
                             DESKTOP, SAVER, DIA, ALLOWED_KEYS)


class MemoryBackend:
    def __init__(self, dia=True, desktop=True):
        self.dia, self.desktop = dia, desktop
        self.values = {
            DESKTOP: {'picture-uri': 'file:///old-light.png', 'picture-uri-dark': 'file:///old-dark.png', 'picture-options': 'scaled'},
            SAVER: {'picture-uri': 'file:///old-lock.png', 'picture-options': 'zoom', 'lock-enabled': True, 'lock-delay': 0},
            DIA: {},
        }
        for prefix in ('desktop', 'lock'):
            self.values[DIA].update({prefix+'-mode': 'slideshow', prefix+'-single-uri': 'file:///old.png',
                prefix+'-files': ['file:///old1.png', 'file:///old2.png'], prefix+'-folder': 'file:///old-folder',
                prefix+'-recursive': True, prefix+'-interval': 7, prefix+'-shuffle': False,
                prefix+'-paused': True, prefix+'-current-uri': 'file:///old.png'})
        self.values[DIA]['clock-visible'] = True
        self.calls = []
        self.fail = None

    def desktop_available(self): return self.desktop
    def dia_active(self): return self.dia
    def read(self, schema, key): return copy.deepcopy(self.values[schema][key])
    def preflight(self, plan):
        for schema, values in plan.items():
            if not set(values) <= ALLOWED_KEYS.get(schema, set()): raise ValueError('not a background key')
    def write(self, schema, values):
        self.calls.append((schema, copy.deepcopy(values)))
        if self.fail == schema:
            self.fail = None
            # Simulate a partial backend failure too, not only a no-op.
            self.values[schema].update(values)
            raise OSError('simulated storage failure')
        self.values[schema].update(copy.deepcopy(values))


class WallpaperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bundle = self.root / 'bundle'; self.bundle.mkdir()
        self.picture = self.bundle / 'kupari.png'
        image = QImage(32, 18, QImage.Format.Format_RGB32)
        image.fill(QColor('#ef986e')); self.assertTrue(image.save(str(self.picture)))
        self.other = self.bundle / 'halla.png'
        image.fill(QColor('#a3cfe9')); self.assertTrue(image.save(str(self.other)))
        self.backend = MemoryBackend()
        self.manager = WallpaperManager(self.bundle, self.root / 'data', self.backend)
        self.before = copy.deepcopy(self.backend.values)

    def tearDown(self): self.temporary.cleanup()

    def test_startup_and_listing_never_write_system_settings(self):
        self.assertEqual(len(self.manager.library.list()), 2)
        self.assertEqual(self.manager.capabilities(), (True, True))
        self.manager.current('desktop'); self.manager.current('lock')
        self.assertEqual(self.backend.calls, [])
        self.assertFalse(self.manager.backup.exists())

    def test_desktop_only_sets_both_variants_and_leaves_lock_unchanged(self):
        self.manager.apply([self.picture], 'desktop')
        values = self.backend.values
        self.assertEqual(values[DESKTOP]['picture-uri'], values[DESKTOP]['picture-uri-dark'])
        self.assertEqual(values[DESKTOP]['picture-options'], 'zoom')
        self.assertEqual(values[SAVER], self.before[SAVER])
        self.assertEqual({k:v for k,v in values[DIA].items() if k.startswith('lock-')},
                         {k:v for k,v in self.before[DIA].items() if k.startswith('lock-')})
        self.assertTrue(values[DIA]['clock-visible'])
        self.assertEqual(values[DIA]['desktop-mode'], 'single')

    def test_lock_only_never_changes_desktop_or_security(self):
        self.manager.apply([self.picture], 'lock')
        self.assertEqual(self.backend.values[DESKTOP], self.before[DESKTOP])
        self.assertTrue(self.backend.values[SAVER]['lock-enabled'])
        self.assertEqual(self.backend.values[SAVER]['lock-delay'], 0)
        self.assertTrue(self.backend.values[DIA]['clock-visible'])
        self.assertEqual(self.backend.values[DIA]['lock-mode'], 'single')

    def test_both_then_restore_exact_original_configuration(self):
        self.manager.apply([self.picture], 'both')
        self.assertEqual(self.backend.values[DIA]['desktop-single-uri'], self.backend.values[DIA]['lock-single-uri'])
        self.manager.restore()
        self.assertEqual(self.backend.values, self.before)

    def test_rotation_uses_stable_copies_and_77_minutes(self):
        self.manager.apply([self.picture, self.other], 'lock', 'slideshow', 77, True)
        values = self.backend.values[DIA]
        self.assertEqual(values['lock-interval'], 77)
        self.assertEqual(values['lock-mode'], 'slideshow')
        self.assertFalse(values['lock-paused'])
        self.assertEqual(values['lock-folder'], '')
        self.assertEqual(len(values['lock-files']), 2)
        self.assertTrue(all('/wallpapers/files/' in uri for uri in values['lock-files']))
        self.assertEqual(self.backend.values[DESKTOP], self.before[DESKTOP])

    def test_backend_failure_rolls_back_all_channels(self):
        self.backend.fail = SAVER
        with self.assertRaises(OSError): self.manager.apply([self.picture], 'both')
        self.assertEqual(self.backend.values, self.before)

    def test_failed_backup_aborts_before_any_system_write(self):
        with patch('asaa.wallpapers.atomic_json', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.manager.apply([self.picture], 'both')
        self.assertEqual(self.backend.values, self.before)
        self.assertEqual(self.backend.calls, [])

    def test_failed_app_commit_restores_background_and_security(self):
        commit=unittest.mock.Mock(side_effect=OSError('state disk full'))
        with self.assertRaises(OSError):self.manager.apply([self.other],'both',commit=commit)
        commit.assert_called_once_with()
        self.assertEqual(self.backend.values,self.before)

    def test_successful_app_commit_runs_after_background_readback(self):
        def commit():
            self.assertEqual(self.backend.values[DIA]['desktop-mode'],'single')
            self.assertEqual(self.backend.values[SAVER],self.before[SAVER])
        self.manager.apply([self.other],'desktop',commit=commit)

    def test_backend_failure_does_not_commit_application_state(self):
        commit=unittest.mock.Mock();self.backend.fail=DESKTOP
        with self.assertRaises(OSError):self.manager.apply([self.other],'desktop',commit=commit)
        commit.assert_not_called();self.assertEqual(self.backend.values,self.before)

    def test_theme_default_uses_matching_bundled_record(self):
        atomic_json(self.bundle/'catalog.json',{'version':1,'wallpapers':[
            {'file':'kupari.png','theme':'copper','title':'Kupari'},
            {'file':'halla.png','theme':'frost','title':'Halla'}]})
        self.assertEqual(self.manager.library.for_theme('copper').path,self.picture)
        self.assertEqual(self.manager.library.for_theme('frost').path,self.other)
        self.assertEqual(self.backend.calls,[])

    def test_missing_theme_default_does_not_pick_unrelated_artwork(self):
        with self.assertRaises(ValueError):self.manager.library.for_theme('frost')
        self.assertEqual(self.backend.calls,[])

    def test_theme_follow_default_and_old_state_migration_are_non_mutating(self):
        state=State(self.root/'state.json');state.commit(state.data)
        old=copy.deepcopy(state.data)
        old['settings'].pop('wallpaper_follow_theme');old['settings'].pop('wallpaper_theme_target')
        atomic_json(state.path,old);raw=state.path.read_bytes()
        loaded=State(state.path)
        self.assertTrue(loaded.settings['wallpaper_follow_theme'])
        self.assertEqual(loaded.settings['wallpaper_theme_target'],'desktop')
        self.assertEqual(loaded.path.read_bytes(),raw)
        self.assertEqual(loaded.data['geometry'],old['geometry'])

    def test_explicit_keep_policy_survives_reopen(self):
        state=State(self.root/'state.json');state.configure({'wallpaper_follow_theme':False,'wallpaper_theme_target':'both'})
        loaded=State(state.path)
        self.assertFalse(loaded.settings['wallpaper_follow_theme'])
        self.assertEqual(loaded.settings['wallpaper_theme_target'],'both')

    def test_bundled_theme_assets_metadata_and_pixels_match(self):
        bundle=Path(__file__).resolve().parents[1]/'assets/wallpapers'
        library=WallpaperLibrary(bundle,self.root/'assets-test')
        payload=json.loads((bundle/'catalog.json').read_text())
        for theme in THEMES:
            item=library.for_theme(theme)
            record=next(record for record in payload['wallpapers'] if record['theme']==theme)
            self.assertEqual(image_size(item.path),(record['width'],record['height']))
            self.assertTrue((bundle/record['prompt']).is_file())

    def test_no_extension_exposes_desktop_only(self):
        self.backend.dia = False
        for target in ('lock', 'both'):
            with self.assertRaises(ValueError): self.manager.apply([self.picture], target)
        with self.assertRaises(ValueError): self.manager.apply([self.picture, self.other], 'desktop', 'slideshow')
        self.assertEqual(self.backend.calls, [])
        self.manager.apply([self.picture], 'desktop')
        self.assertEqual([schema for schema, _ in self.backend.calls], [DESKTOP])

    def test_invalid_selection_or_corrupt_image_leaves_system_alone(self):
        cases = [([], 'desktop', 'single', 77), ([self.picture,self.other], 'desktop', 'single', 77),
                 ([self.picture], 'desktop', 'slideshow', 77), ([self.picture], 'desktop', 'single', 78),
                 ([self.picture], 'unknown', 'single', 77)]
        for paths, target, mode, interval in cases:
            with self.assertRaises(ValueError): self.manager.apply(paths, target, mode, interval)
        atomic_json(self.root / 'bad.png', {'not':'an image'})
        with self.assertRaises(ValueError): self.manager.apply([self.root/'bad.png'], 'desktop')
        self.assertEqual(self.backend.calls, [])

    def test_import_is_non_destructive_and_deduplicated(self):
        before = self.picture.read_bytes()
        imported = self.manager.library.add(self.picture)
        self.manager.library.add(self.picture)
        self.assertEqual(self.picture.read_bytes(), before)
        self.assertEqual(imported.read_bytes(), before)
        self.assertEqual(len(json.loads(self.manager.library.imports.read_text())), 1)
        self.assertEqual(len(self.manager.library.list()), 2)

    def test_repository_cannot_escape_its_folder_or_symlink_to_other_images(self):
        folder = self.root / 'repo'; folder.mkdir()
        for filename in ('../bundle/kupari.png', str(self.picture)):
            atomic_json(folder/'catalog.json', {'version':1,'wallpapers':[{'file':filename}]})
            with self.assertRaises(ValueError): self.manager.library.catalog(folder,'Teema-repo')
        (folder/'link.png').symlink_to(self.picture)
        atomic_json(folder/'catalog.json', {'version':1,'wallpapers':[{'file':'link.png'}]})
        with self.assertRaises(ValueError): self.manager.library.catalog(folder,'Teema-repo')

    def test_backup_cannot_modify_lock_settings(self):
        atomic_json(self.manager.backup, {'version':1,'settings':{SAVER:{'lock-enabled':False}}})
        with self.assertRaises(ValueError): self.manager.restore()
        self.assertEqual(self.backend.calls, [])

    def test_old_state_gains_wallpaper_defaults_without_changing_widgets(self):
        state = State(self.root/'state.json')
        old = copy.deepcopy(state.data)
        for key in ('wallpaper_directory','wallpaper_mode','wallpaper_interval','wallpaper_shuffle'):
            old['settings'].pop(key)
        old['settings']['widgets']['star'] = False
        old['geometry']['shadow'] = [1580,62]
        old['notes']['2026-10-07'] = 'Merkintä'
        atomic_json(state.path, old)
        loaded = State(state.path)
        self.assertEqual(loaded.settings['wallpaper_interval'],77)
        self.assertEqual(loaded.settings['wallpaper_mode'],'single')
        self.assertFalse(loaded.settings['widgets']['star'])
        self.assertEqual(loaded.geometry('shadow'),[1580,62])
        self.assertEqual(loaded.data['notes'],old['notes'])

    def test_state_rejects_invalid_wallpaper_preferences(self):
        state = State(self.root/'state.json')
        for changes in ({'wallpaper_interval':True},{'wallpaper_interval':78},{'wallpaper_directory':123},
                        {'wallpaper_mode':'surprise'},{'wallpaper_shuffle':1},
                        {'wallpaper_follow_theme':1},{'wallpaper_theme_target':'unknown'}):
            with self.assertRaises(ValueError): state.configure(changes)

    def test_image_validation_reads_pixels(self):
        self.assertEqual(image_size(self.picture),(32,18))


if __name__ == '__main__': unittest.main()
