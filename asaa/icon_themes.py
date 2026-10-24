"""Bundled user icon themes and explicit, reversible GNOME appearance changes.

Opening the application only reads capabilities. Desktop writes, installation
and launcher fixes require an explicit action or an enabled shared-theme policy.
The launcher installer never runs during an automatic theme change.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from .state import atomic_json

INTERFACE = 'org.gnome.desktop.interface'
ICON_KEY = 'icon-theme'
THEMES = {'copper': 'Ajanlaskut-Kupari', 'frost': 'Ajanlaskut-Halla', 'ubuntu': 'Ajanlaskut-Ubuntu',
          'ubuntu2610_dark': 'Ajanlaskut-Ubuntu-2610-Dark', 'blood': 'Ajanlaskut-Veriyo'}


def valid_theme_name(value):
    return isinstance(value, str) and re.fullmatch(r'[^/\\\x00-\x1f]{1,256}', value) is not None


def validate_plan(plan):
    if (not isinstance(plan, dict) or set(plan) != {INTERFACE}
        or not isinstance(plan[INTERFACE], dict) or set(plan[INTERFACE]) != {ICON_KEY}
        or not valid_theme_name(plan[INTERFACE][ICON_KEY])):
        raise ValueError('Varmuuskopio saa sisältää vain GNOMEn kuvaketeeman.')


class GioIconBackend:
    """Use GNOME's installed schema and write only its icon-theme key."""
    def __init__(self):
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        source = Gio.SettingsSchemaSource.get_default()
        self.definition = source.lookup(INTERFACE, True) if source else None
        if self.definition is None or not self.definition.has_key(ICON_KEY):
            raise ValueError('GNOMEn kuvaketeema-asetusta ei löydy.')
        self.settings = Gio.Settings.new_full(self.definition, None, None)

    def desktop_available(self):
        return self.settings.is_writable(ICON_KEY)

    def read(self, schema, key):
        if schema != INTERFACE or key != ICON_KEY:
            raise ValueError('Tuntematon kuvaketeema-asetus.')
        return self.settings.get_string(ICON_KEY)

    def default_theme(self):
        value = self.settings.get_default_value(ICON_KEY)
        if value is None:
            raise ValueError('Järjestelmän oletuskuvaketeemaa ei löydy.')
        return value.unpack()

    def preflight(self, plan):
        validate_plan(plan)
        value = self.GLib.Variant('s', plan[INTERFACE][ICON_KEY])
        if not self.desktop_available() or not self.definition.get_key(ICON_KEY).range_check(value):
            raise ValueError('GNOMEn kuvaketeemaa ei voi muuttaa tässä työpöytäympäristössä.')

    def write(self, schema, values):
        self.preflight({schema: values})
        self.settings.delay()
        try:
            if not self.settings.set_string(ICON_KEY, values[ICON_KEY]):
                raise OSError('Kuvaketeemaa ei voitu tallentaa.')
            self.settings.apply(); self.Gio.Settings.sync()
            if self.read(schema, ICON_KEY) != values[ICON_KEY]:
                raise OSError('Kuvaketeeman tallennuksen tarkistus epäonnistui.')
        except Exception:
            self.settings.revert()
            raise


class IconThemeManager:
    def __init__(self, bundled, data_dir, backend=None, data_home=None, installer=None):
        self.bundled = Path(bundled)
        self.backup = Path(data_dir) / 'icon-theme-previous.json'
        self.data_home = Path(data_home if data_home is not None else
            (os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')).expanduser()
        if not self.data_home.is_absolute():
            raise ValueError('XDG_DATA_HOME on oltava absoluuttinen polku.')
        self.backend = backend
        self.installer = installer
        self.error = ''
        if backend is None:
            try: self.backend = GioIconBackend()
            except (ImportError, ValueError, RuntimeError, OSError) as error:
                self.error = 'GNOME-kuvaketeemat eivät ole käytettävissä: ' + str(error)

    def available(self):
        return bool(self.backend and self.backend.desktop_available())

    def current(self):
        if not self.available(): return 'Ei saatavilla tässä työpöytäympäristössä'
        return self.backend.read(INTERFACE, ICON_KEY)

    def system_default(self):
        if not self.available():
            raise ValueError(self.error or 'Kuvaketeeman vaihto tarvitsee GNOME-työpöydän.')
        value = self.backend.default_theme()
        validate_plan({INTERFACE: {ICON_KEY: value}})
        return value

    def default_available(self):
        try:
            self.backend.preflight({INTERFACE: {ICON_KEY: self.system_default()}})
        except (AttributeError, ValueError, RuntimeError, OSError, TypeError):
            return False
        return True

    def _installer(self):
        if self.installer is None:
            path = self.bundled / 'install.py'
            if not path.is_file(): raise ValueError('Sovelluksen kuvaketeemojen asennin puuttuu.')
            spec = importlib.util.spec_from_file_location('ajanlaskut_bundled_icon_installer', path)
            installer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(installer)
            self.installer = installer
        return self.installer

    def _install_theme(self, theme):
        if theme not in THEMES: raise ValueError('Tuntematon kuvaketeema.')
        name = THEMES[theme]
        source = self.bundled / name
        if not (source / 'index.theme').is_file():
            raise ValueError('Sovelluksen kuvaketeema puuttuu: ' + name)
        try: self._installer().install_theme(source, self.data_home / 'icons' / name)
        except subprocess.CalledProcessError as error:
            raise OSError('Kuvaketeeman välimuistin päivitys epäonnistui: ' + str(error)) from error

    def install(self, all_apps=False):
        """Explicit installation and launcher repair, without global activation."""
        if type(all_apps) is not bool: raise ValueError('Virheellinen käynnistinkuvakkeiden valinta.')
        for theme in THEMES: self._install_theme(theme)
        try: return self._installer().fix_app_launchers(self.data_home, all_apps=all_apps)
        except subprocess.CalledProcessError as error:
            raise OSError('Sovelluskäynnistimien päivitys epäonnistui: ' + str(error)) from error

    def launcher_backup_exists(self):
        path = self.data_home / 'ajanlaskut-icon-themes/launchers.json'
        try: return path.is_file() and bool(json.loads(path.read_text(encoding='utf-8')))
        except (OSError, ValueError): return False

    def launcher_registry_exists(self):
        path = self.data_home / 'ajanlaskut-icon-themes/launchers.json'
        return path.exists() or path.is_symlink()

    def restore_launchers(self):
        return self._installer().restore_app_launchers(self.data_home)

    def _read_backup(self):
        if self.backup.is_symlink(): raise ValueError('Kuvaketeeman varmuuskopio on symbolinen linkki.')
        payload = json.loads(self.backup.read_text(encoding='utf-8'))
        if not isinstance(payload, dict) or payload.get('version') != 1:
            raise ValueError('Kuvaketeeman varmuuskopio ei ole tuettu.')
        validate_plan(payload.get('settings'))
        return payload['settings']

    def transaction(self, plan, commit=None, rollback_cleanup=None):
        written = False
        try:
            validate_plan(plan)
            if not self.available():
                raise ValueError(self.error or 'Kuvaketeeman vaihto tarvitsee GNOME-työpöydän.')
            self.backend.preflight(plan)
            previous = {INTERFACE: {ICON_KEY: self.backend.read(INTERFACE, ICON_KEY)}}
            written = True
            self.backend.write(INTERFACE, plan[INTERFACE])
            if commit is not None: commit()
        except Exception as error:
            if written:
                try: self.backend.write(INTERFACE, previous[INTERFACE])
                except Exception as recovery:
                    raise OSError(f'{error}\nAiemman kuvaketeeman palautus epäonnistui: {recovery}') from error
            # Only a confirmed recovery may discard a first-use undo snapshot.
            # If recovery itself fails, keep it available for explicit restore.
            if rollback_cleanup is not None:
                try: rollback_cleanup()
                except Exception as recovery:
                    raise OSError(f'{error}\nKuvaketeeman varmuuskopion poisto epäonnistui: {recovery}') from error
            raise

    def apply(self, theme, commit=None):
        if theme not in THEMES: raise ValueError('Tuntematon kuvaketeema.')
        plan = {INTERFACE: {ICON_KEY: THEMES[theme]}}
        self._apply_with_backup(plan, commit, theme=theme)

    def apply_default(self, commit=None):
        plan = {INTERFACE: {ICON_KEY: self.system_default()}}
        self._apply_with_backup(plan, commit)

    def _apply_with_backup(self, plan, commit=None, theme=None):
        validate_plan(plan)
        if not self.available():
            raise ValueError(self.error or 'Kuvaketeeman vaihto tarvitsee GNOME-työpöydän.')
        self.backend.preflight(plan)
        if theme is not None: self._install_theme(theme)
        # Keep the original desktop theme across subsequent Kupari/Halla changes.
        # Persist before any desktop write, and reject a damaged existing backup.
        created_backup = False
        if self.backup.exists() or self.backup.is_symlink(): self._read_backup()
        else:
            previous = {INTERFACE: {ICON_KEY: self.backend.read(INTERFACE, ICON_KEY)}}
            validate_plan(previous)
            atomic_json(self.backup, {'version': 1, 'settings': previous})
            created_backup = True
        self.transaction(plan, commit, rollback_cleanup=self.backup.unlink if created_backup else None)

    def restore(self, commit=None):
        plan = self._read_backup()
        # Retire the active backup transactionally. A failed desktop/settings
        # write restores its exact file; a successful restore begins a new
        # lifecycle, so the next apply remembers the then-current desktop theme.
        descriptor, name = tempfile.mkstemp(prefix='.icon-theme-restored-', dir=self.backup.parent)
        os.close(descriptor)
        retired = Path(name)
        try: self.backup.replace(retired)
        except Exception:
            retired.unlink(missing_ok=True)
            raise
        try: self.transaction(plan, commit)
        except Exception as error:
            try: retired.replace(self.backup)
            except Exception as recovery:
                raise OSError(f'{error}\nKuvaketeeman varmuuskopion palautus epäonnistui: {recovery}') from error
            raise
        # The active backup is already consumed even if cleanup is unavailable.
        # Never report an already committed restore as a failed desktop change.
        try: retired.unlink()
        except OSError: pass
