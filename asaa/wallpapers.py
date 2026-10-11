"""Local wallpaper library and explicit, reversible GNOME background changes.

No system writes at startup, no downloads, and no authentication/locking changes.
Theme changes can explicitly follow the selected desktop/lock wallpaper policy.
Dia Wall 77 supplies GNOME's independent lock-screen background and slideshows.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import unquote, urlparse

from PyQt6.QtGui import QImageReader
from .state import atomic_json

DESKTOP = 'org.gnome.desktop.background'
SAVER = 'org.gnome.desktop.screensaver'
DIA = 'org.gnome.shell.extensions.dia-wall-77'
DIA_UUID = 'dia-wall-77@jakke77.local'
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
# A saved backup may only restore background keys, never lock/security settings.
ALLOWED_KEYS = {
    DESKTOP: {'picture-uri', 'picture-uri-dark', 'picture-options'},
    SAVER: {'picture-uri', 'picture-options'},
    DIA: {f'{prefix}-{suffix}' for prefix in ('desktop', 'lock') for suffix in
          ('mode', 'single-uri', 'files', 'folder', 'recursive', 'interval',
           'shuffle', 'paused', 'current-uri')},
}


@dataclass(frozen=True)
class Wallpaper:
    path: Path
    title: str
    theme: str = ''
    description: str = ''
    source: str = 'Oma kuva'


def image_size(path):
    path = Path(path)
    if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError('Valitse PNG-, JPEG-, WebP- tai BMP-kuva.')
    if path.stat().st_size > 80 * 1024 * 1024:
        raise ValueError('Kuva on liian suuri (enintään 80 Mt).')
    reader = QImageReader(str(path))
    size = reader.size()
    if not size.isValid() or size.width() * size.height() > 80_000_000:
        raise ValueError('Kuvaa ei voida lukea tai sen tarkkuus on liian suuri.')
    if not reader.canRead() or reader.read().isNull():
        raise ValueError('Kuva on vioittunut tai sen tiedostomuotoa ei tueta.')
    return size.width(), size.height()


class WallpaperLibrary:
    def __init__(self, bundled, data_dir):
        self.bundled = Path(bundled)
        self.root = Path(data_dir) / 'wallpapers'
        self.imports = self.root / 'imports.json'

    def catalog(self, folder, source):
        folder = Path(folder).resolve()
        manifest = folder / 'catalog.json'
        if not manifest.is_file():
            return [Wallpaper(p, p.stem.replace('-', ' '), source=source)
                    for p in sorted(folder.iterdir())
                    if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
        payload = json.loads(manifest.read_text(encoding='utf-8'))
        if not isinstance(payload, dict) or payload.get('version') != 1 or not isinstance(payload.get('wallpapers'), list):
            raise ValueError('Teemakansion catalog.json ei ole tuettua muotoa.')
        items = []
        for record in payload['wallpapers']:
            if not isinstance(record, dict) or not isinstance(record.get('file'), str):
                raise ValueError('Teemakansion kuvatiedoissa on virhe.')
            relative = Path(record['file'])
            path = (folder / relative).resolve()
            if relative.is_absolute() or not path.is_relative_to(folder):
                raise ValueError('Teemakuvan polku ei saa poistua teemakansiosta.')
            if not isinstance(record.get('title', path.stem), str):
                raise ValueError('Teemakuvan nimen pitää olla tekstiä.')
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                items.append(Wallpaper(path, record.get('title', path.stem),
                    str(record.get('theme', '')), str(record.get('description', '')), source))
        return items

    def list(self, extra=''):
        items = self.catalog(self.bundled, 'Sovelluksen teema')
        if extra:
            folder = Path(extra).expanduser()
            if not folder.is_dir(): raise ValueError('Valittua teemakansiota ei löydy.')
            items.extend(self.catalog(folder, 'Teema-repo'))
        if self.imports.exists():
            payload = json.loads(self.imports.read_text(encoding='utf-8'))
            for record in payload:
                path = (self.root / record['file']).resolve()
                if path.is_relative_to(self.root.resolve()) and path.is_file():
                    items.append(Wallpaper(path, record['title']))
        # The same artwork can be bundled and live in the independent theme repo.
        unique = {}
        for item in items:
            digest = sha256(item.path.read_bytes()).hexdigest()
            unique.setdefault(digest, item)
        return list(unique.values())

    def for_theme(self, theme):
        """The bundled, versioned theme default is independent of a moved repo."""
        item = next((item for item in self.catalog(self.bundled, 'Sovelluksen teema')
                     if item.theme == theme), None)
        if item is None: raise ValueError('Tälle teemalle ei löydy oletustaustakuvaa.')
        return item

    def preserve(self, path):
        """A stable copy survives moving the repo or uninstalling an old version."""
        path = Path(path).resolve()
        image_size(path)
        digest = sha256(path.read_bytes()).hexdigest()
        directory = self.root / 'files'
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / (digest + path.suffix.lower())
        if target.exists() and sha256(target.read_bytes()).hexdigest() == digest:
            return target
        descriptor, name = tempfile.mkstemp(prefix='.image-', dir=directory)
        try:
            with os.fdopen(descriptor, 'wb') as stream, path.open('rb') as source:
                shutil.copyfileobj(source, stream)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            Path(name).unlink(missing_ok=True)
        return target

    def add(self, path):
        target = self.preserve(path)
        records = json.loads(self.imports.read_text(encoding='utf-8')) if self.imports.exists() else []
        relative = str(target.relative_to(self.root))
        if not any(item['file'] == relative for item in records):
            records.append({'file': relative, 'title': Path(path).stem.replace('-', ' ')})
            atomic_json(self.imports, records)
        return target


class GioBackend:
    """Read actual installed schemas; only an active extension is used."""
    def __init__(self):
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.schemas = Gio.SettingsSchemaSource.get_default()
        self.objects = {}
        data_home = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
        directories = [data_home, *[Path(p) for p in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if p]]
        for directory in directories:
            folder = directory / 'gnome-shell/extensions' / DIA_UUID / 'schemas'
            if (folder / 'gschemas.compiled').is_file():
                self.schemas = Gio.SettingsSchemaSource.new_from_directory(str(folder), self.schemas, False)
                break

    def object(self, schema):
        if schema not in self.objects:
            definition = self.schemas.lookup(schema, True) if self.schemas else None
            if definition is None: raise ValueError('GNOMEn taustakuva-asetuksia ei löydy.')
            self.objects[schema] = self.Gio.Settings.new_full(definition, None, None)
        return self.objects[schema]

    def desktop_available(self):
        try:
            keys = self.object(DESKTOP).list_keys()
            return all(key in keys for key in ALLOWED_KEYS[DESKTOP])
        except ValueError: return False

    def dia_active(self):
        try:
            self.object(DIA)
            bus = self.Gio.bus_get_sync(self.Gio.BusType.SESSION, None)
            result = bus.call_sync('org.gnome.Shell.Extensions',
                '/org/gnome/Shell/Extensions', 'org.gnome.Shell.Extensions',
                'GetExtensionInfo', self.GLib.Variant('(s)', (DIA_UUID,)),
                None, self.Gio.DBusCallFlags.NONE, 1500, None)
            info = result.unpack()[0]
            return info.get('state') == 1 and bool(info.get('enabled'))
        except (ValueError, self.GLib.Error): return False

    def read(self, schema, key):
        return self.object(schema).get_value(key).unpack()

    def preflight(self, plan):
        for schema, values in plan.items():
            settings = self.object(schema)
            definition = settings.props.settings_schema
            for key, value in values.items():
                if key not in ALLOWED_KEYS.get(schema, set()) or not definition.has_key(key):
                    raise ValueError('Tuntematon taustakuva-asetus.')
                kind = definition.get_key(key).get_value_type().dup_string()
                variant = self.GLib.Variant(kind, value)
                if not settings.is_writable(key) or not definition.get_key(key).range_check(variant):
                    raise ValueError('Taustakuva-asetusta ei voi muuttaa: ' + key)

    def write(self, schema, values):
        settings = self.object(schema)
        definition = settings.props.settings_schema
        settings.delay()
        try:
            for key, value in values.items():
                kind = definition.get_key(key).get_value_type().dup_string()
                if not settings.set_value(key, self.GLib.Variant(kind, value)):
                    raise OSError('Taustakuvaa ei voitu tallentaa: ' + key)
            settings.apply(); self.Gio.Settings.sync()
            for key, value in values.items():
                if self.read(schema, key) != value:
                    raise OSError('Taustakuva-asetuksen tarkistus epäonnistui: ' + key)
        except Exception:
            settings.revert()
            raise


class WallpaperManager:
    def __init__(self, bundled, data_dir, backend=None):
        self.library = WallpaperLibrary(bundled, data_dir)
        self.backup = Path(data_dir) / 'wallpaper-previous.json'
        self.backend = backend
        self.error = ''
        if backend is None:
            try: self.backend = GioBackend()
            except (ImportError, ValueError, RuntimeError, OSError) as error:
                self.error = 'GNOME-taustakuvat eivät ole käytettävissä: ' + str(error)

    def capabilities(self):
        desktop = bool(self.backend and self.backend.desktop_available())
        dia = bool(desktop and self.backend.dia_active())
        return desktop, dia

    def current(self, target, capabilities=None):
        desktop, dia = self.capabilities() if capabilities is None else capabilities
        if not desktop: return 'Ei saatavilla tässä työpöytäympäristössä'
        schema, key = DESKTOP, 'picture-uri-dark'
        if target == 'lock' and dia and self.backend.read(DIA, 'lock-mode') != 'off':
            schema, key = DIA, 'lock-current-uri'
        uri = self.backend.read(schema, key)
        parsed = urlparse(uri)
        if parsed.scheme != 'file': return uri or 'Työpöydän tausta'
        path = Path(unquote(parsed.path))
        if path.parent.resolve() == (self.library.root/'files').resolve():
            try:
                for item in self.library.list():
                    if sha256(item.path.read_bytes()).hexdigest() == path.stem:
                        return item.title
            except (OSError, ValueError, TypeError, KeyError): pass
        return path.name

    def plan(self, paths, target, mode='single', interval=77, shuffle=True):
        if target not in ('desktop', 'lock', 'both') or mode not in ('single', 'slideshow'):
            raise ValueError('Tuntematon taustakuvavalinta.')
        if type(interval) is not int or not 1 <= interval <= 77 or type(shuffle) is not bool:
            raise ValueError('Vaihtovälin pitää olla 1–77 minuuttia.')
        if not paths: raise ValueError('Valitse ensin taustakuva.')
        if mode == 'single' and len(paths) != 1:
            raise ValueError('Yhden kuvan tilassa valitse vain yksi kuva.')
        if mode == 'slideshow' and len(paths) < 2:
            raise ValueError('Vaihtuviin taustakuviin tarvitaan vähintään kaksi kuvaa. Lisää omia kuvia tai teema-repo.')
        desktop, dia = self.capabilities()
        if not desktop: raise ValueError(self.error or 'Taustakuvan vaihto tarvitsee GNOME-työpöydän.')
        if (target != 'desktop' or mode == 'slideshow') and not dia:
            raise ValueError('Erillinen lukituskuva ja vaihtuvat kuvat tarvitsevat käytössä olevan Dia Wall 77 -lisäosan. Tavallinen GNOME käyttää lukitusnäytöllä työpöydän taustaa.')
        uris = [self.library.preserve(path).as_uri() for path in paths]
        plan = {}
        if dia:
            values = {}
            for prefix in (('desktop', 'lock') if target == 'both' else (target,)):
                values.update({prefix+'-mode': mode, prefix+'-single-uri': uris[0],
                    prefix+'-current-uri': uris[0]})
                if mode == 'slideshow':
                    values.update({prefix+'-files': uris, prefix+'-folder': '',
                        prefix+'-recursive': False, prefix+'-interval': interval,
                        prefix+'-shuffle': shuffle, prefix+'-paused': False})
            plan[DIA] = values
        if target in ('desktop', 'both'):
            plan[DESKTOP] = {'picture-uri': uris[0], 'picture-uri-dark': uris[0], 'picture-options': 'zoom'}
        if target in ('lock', 'both'):
            plan[SAVER] = {'picture-uri': uris[0], 'picture-options': 'zoom'}
        return plan

    def transaction(self, plan):
        self.backend.preflight(plan)
        previous = {schema: {key: self.backend.read(schema, key) for key in values}
                    for schema, values in plan.items()}
        written = []
        try:
            for schema, values in plan.items():
                written.append(schema)
                self.backend.write(schema, values)
        except Exception as error:
            failures = []
            for schema in reversed(written):
                try: self.backend.write(schema, previous[schema])
                except Exception as recovery: failures.append(str(recovery))
            if failures: raise OSError(f'{error}\nAiemman taustan palautus epäonnistui: {"; ".join(failures)}') from error
            raise

    def apply(self, paths, target, mode='single', interval=77, shuffle=True, commit=None):
        plan = self.plan(paths, target, mode, interval, shuffle)
        self.backend.preflight(plan)
        previous = {schema: {key: self.backend.read(schema, key) for key in values}
                    for schema, values in plan.items()}
        # Persist the undo snapshot BEFORE any system write, including disk-full failures.
        atomic_json(self.backup, {'version': 1, 'settings': previous})
        self.transaction(plan)
        if commit is not None:
            try: commit()
            except Exception as error:
                try: self.transaction(previous)
                except Exception as recovery:
                    raise OSError(f'{error}\nAiemman taustan palautus epäonnistui: {recovery}') from error
                raise

    def restore(self):
        payload = json.loads(self.backup.read_text(encoding='utf-8'))
        if not isinstance(payload, dict) or payload.get('version') != 1 or not isinstance(payload.get('settings'), dict):
            raise ValueError('Taustakuvan varmuuskopio ei ole tuettu.')
        plan = payload['settings']
        if not plan: raise ValueError('Varmuuskopio on tyhjä.')
        if DIA in plan and not self.capabilities()[1]:
            raise ValueError('Palautus tarvitsee käytössä olevan Dia Wall 77 -lisäosan.')
        for schema, values in plan.items():
            if not isinstance(values, dict) or not values or not set(values) <= ALLOWED_KEYS.get(schema, set()):
                raise ValueError('Varmuuskopio sisältää muita kuin taustakuva-asetuksia.')
        self.transaction(plan)
