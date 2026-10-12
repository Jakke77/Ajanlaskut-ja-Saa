#!/usr/bin/env python3
"""Install the three icon themes for the current user, without sudo."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
THEMES = {'copper': 'Ajanlaskut-Kupari', 'frost': 'Ajanlaskut-Halla', 'ubuntu': 'Ajanlaskut-Ubuntu'}
MARKER = '.ajanlaskut-icons'
INSTALL_MANIFEST = '.ajanlaskut-installed.json'


def digest(contents):
    return hashlib.sha256(contents).hexdigest()


def atomic_bytes(path, contents):
    if path.is_symlink():
        raise ValueError(f'Tiedosto on symbolinen linkki: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.ajanlaskut-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(contents)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def install_theme(source, destination):
    """Update unchanged managed assets; preserve unrelated files and user edits."""
    managed = {}
    if destination.is_symlink():
        raise ValueError(f'Kohde on symbolinen linkki: {destination}')
    if destination.exists():
        if not destination.is_dir() or not (destination / MARKER).is_file():
            raise ValueError(f'Kohteessa on aiempi tunnistamaton teema: {destination}')
        for path in destination.rglob('*'):
            if path.is_symlink():
                raise ValueError(f'Kohteessa on symbolinen linkki: {path}')
        manifest = destination / INSTALL_MANIFEST
        if manifest.exists():
            managed = json.loads(manifest.read_text(encoding='utf-8'))
            if not isinstance(managed, dict):
                raise ValueError(f'Virheellinen asennuksen tarkistustiedosto: {manifest}')
        else:
            # The original zip predates manifests. Only its exact known bytes
            # are eligible for migration; an ownership marker alone is not enough.
            legacy = ROOT / 'legacy-v1-hashes.json'
            if legacy.is_file():
                managed = json.loads(legacy.read_text(encoding='utf-8')).get(destination.name, {})
        for path in source.rglob('*'):
            target = destination / path.relative_to(source)
            if path.is_file() and target.exists():
                relative = str(path.relative_to(source))
                if not target.is_file():
                    raise ValueError(f'Tiedostoa on muokattu, säilytä tai siirrä se ensin: {target}')
                current = target.read_bytes()
                if current != path.read_bytes() and digest(current) != managed.get(relative):
                    raise ValueError(f'Tiedostoa on muokattu, säilytä tai siirrä se ensin: {target}')
            elif path.is_dir() and target.exists() and not target.is_dir():
                raise ValueError(f'Hakemiston kohdalla on tiedosto: {target}')
    shutil.copytree(source, destination, dirs_exist_ok=True)
    hashes = {str(path.relative_to(source)): digest(path.read_bytes()) for path in source.rglob('*') if path.is_file()}
    atomic_bytes(destination / INSTALL_MANIFEST, (json.dumps(hashes, indent=2, sort_keys=True) + '\n').encode())
    cache = shutil.which('gtk-update-icon-cache')
    if cache:
        subprocess.run([cache, '--force', '--ignore-theme-index', str(destination)], check=True)
    print(f'Asennettu: {destination}')


def match_widget(data_home):
    path = data_home / 'ajanlaskut-ja-saa' / 'state.json'
    try:
        key = json.loads(path.read_text(encoding='utf-8'))['settings']['theme']
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f'Widgetin teemaa ei voitu lukea tiedostosta {path}') from error
    if key not in THEMES:
        raise ValueError(f'Widgetin teema ei ole tuettu: {key!r}')
    return key


def activate(theme):
    command = shutil.which('gsettings')
    if not command:
        raise ValueError('gsettings puuttuu. Ota teema käyttöön GNOME Tweaksin Ulkoasu → Kuvakkeet -valinnasta.')
    schema, key = 'org.gnome.desktop.interface', 'icon-theme'
    previous = subprocess.run([command, 'get', schema, key], check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run([command, 'set', schema, key, theme], check=True)
    actual = subprocess.run([command, 'get', schema, key], check=True, capture_output=True, text=True).stdout.strip()
    if actual != repr(theme):
        raise ValueError(f'Teeman käyttöönottoa ei voitu vahvistaa: {actual}')
    print(f'Käytössä: {theme}. Edellinen kuvaketeema: {previous}')


def application_directories(data_home):
    roots = [data_home]
    configured = os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share'
    roots.extend(Path(value) for value in configured.split(':') if value and Path(value).is_absolute())
    roots.extend([Path('/var/lib/snapd/desktop'), data_home / 'flatpak/exports/share', Path('/var/lib/flatpak/exports/share')])
    return list(dict.fromkeys(root / 'applications' for root in roots))


def desktop_fields(contents):
    """Read only the main group, without interpreting or executing Exec."""
    fields = {}
    in_entry = False
    for line in contents.splitlines():
        stripped = line.strip()
        if stripped.startswith('['):
            in_entry = stripped == '[Desktop Entry]'
        elif in_entry and '=' in line and not stripped.startswith('#'):
            key, value = line.split('=', 1)
            fields[key] = value
    return fields


def desktop_entries(data_home, directories=None):
    seen = set()
    for directory in application_directories(data_home) if directories is None else directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob('*.desktop')):
            desktop_id = '-'.join(path.relative_to(directory).parts)
            if desktop_id in seen:
                continue
            seen.add(desktop_id)  # Hidden user shadows must also hide lower entries.
            text = path.read_bytes().decode('utf-8')
            fields = desktop_fields(text)
            if not fields or fields.get('Type', 'Application') != 'Application':
                continue
            if fields.get('Hidden', '').lower() == 'true' or fields.get('NoDisplay', '').lower() == 'true':
                continue
            yield desktop_id, path, text, fields


def current_upstream(data_home, desktop_id, local, directories=None):
    """Look behind our shadow, including hidden entries that mask lower copies."""
    for directory in application_directories(data_home) if directories is None else directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob('*.desktop')):
            if path == local:
                continue
            if '-'.join(path.relative_to(directory).parts) == desktop_id:
                return path
    return None


def themed_app_icon(desktop_id, fields, all_apps=False):
    available = ROOT / THEMES['copper'] / 'scalable/apps'
    icon = fields.get('Icon', '')
    basename = Path(icon).name
    for suffix in ('.svg', '.png', '.xpm', '.jpg'):
        if basename.lower().endswith(suffix):
            basename = basename[:-len(suffix)]
            break
    candidates = ([basename] if '/' not in icon else []) + [desktop_id[:-len('.desktop')], fields.get('X-Flatpak', ''), fields.get('X-SnapInstanceName', ''), basename]
    for candidate in candidates:
        if candidate and Path(candidate).name == candidate and (available / (candidate + '.svg')).is_file():
            return candidate
    if not all_apps:
        return None
    categories = set(fields.get('Categories', '').split(';'))
    families = [({'Graphics'}, 'org.gnome.Loupe'), ({'Video'}, 'org.gnome.Totem'), ({'Audio', 'AudioVideo'}, 'org.gnome.Music'), ({'Game'}, 'applications-games'), ({'Development'}, 'code'), ({'Office'}, 'libreoffice-writer'), ({'Network'}, 'web-browser'), ({'Settings', 'System'}, 'org.gnome.Settings')]
    return next((name for groups, name in families if groups & categories), 'applications-other')


def replace_main_icon(original, icon):
    lines = original.splitlines(keepends=True)
    in_entry = False
    for i, line in enumerate(lines):
        if line.strip().startswith('['):
            in_entry = line.strip() == '[Desktop Entry]'
        elif in_entry and line.startswith('Icon='):
            ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
            lines[i] = 'Icon=' + icon + ending
            return ''.join(lines)
    # A valid launcher can omit Icon. Insert it in the main group.
    for i, line in enumerate(lines):
        if line.strip() == '[Desktop Entry]':
            ending = '\r\n' if line.endswith('\r\n') else '\n'
            lines[i] = line.rstrip('\r\n') + ending + 'Icon=' + icon + ending
            return ''.join(lines)
    raise ValueError('Käynnistimessä ei ole [Desktop Entry] -osiota.')


def launcher_registry(data_home):
    path = data_home / 'ajanlaskut-icon-themes/launchers.json'
    if path.is_symlink():
        raise ValueError(f'Palautustiedosto on symbolinen linkki: {path}')
    registry = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(registry, dict):
        raise ValueError(f'Virheellinen palautustiedosto: {path}')
    for name, record in registry.items():
        if Path(name).name != name or not name.endswith('.desktop') or not isinstance(record, dict):
            raise ValueError(f'Virheellinen käynnistintietue: {name!r}')
        valid_hashes = all(isinstance(record.get(key), str) and len(record[key]) == 64 and set(record[key]) <= set('0123456789abcdef') for key in ('original_hash', 'modified_hash'))
        source = record.get('source')
        if not valid_hashes or type(record.get('had_local')) is not bool or not isinstance(source, str) or not Path(source).is_absolute() or not source.endswith('.desktop'):
            raise ValueError(f'Virheellinen käynnistintietue: {name!r}')
    return path, registry


def write_launcher(local, contents):
    if local.is_symlink():
        raise ValueError(f'Käynnistin on symbolinen linkki: {local}')
    local.parent.mkdir(parents=True, exist_ok=True)
    temporary = local.with_suffix('.desktop.icon-theme-tmp')
    created = False
    try:
        with temporary.open('xb') as stream:
            created = True
            stream.write(contents)
        temporary.replace(local)
    finally:
        if created:
            temporary.unlink(missing_ok=True)


def clear_managed_shadow(local, record):
    backup = local.with_suffix('.desktop.before-icon-theme')
    if backup.is_symlink() or not backup.is_file() or digest(backup.read_bytes()) != record['original_hash']:
        raise ValueError(f'Varmuuskopiota on muokattu: {backup}')
    local.unlink()
    backup.unlink()


def fix_app_launchers(data_home, all_apps=False, directories=None, only=None):
    registry_path, registry = launcher_registry(data_home)
    changed = 0
    unsupported = []
    found = False
    for desktop_id, source, original, fields in desktop_entries(data_home, directories):
        if only is not None and desktop_id not in only:
            continue
        found = True
        icon = themed_app_icon(desktop_id, fields, all_apps)
        if icon is None:
            unsupported.append(desktop_id)
            continue
        local = data_home / 'applications' / desktop_id
        if local.is_symlink():
            raise ValueError(f'Käynnistin on symbolinen linkki: {local}')
        record = registry.get(desktop_id)
        if record and local.exists():
            if digest(local.read_bytes()) != record['modified_hash']:
                raise ValueError(f'Käynnistintä on muokattu asennuksen jälkeen: {local}')
            # Refresh an installer-created shadow from its upstream launcher,
            # so reapplying after a Snap/Flatpak update preserves the new Exec.
            if not record['had_local']:
                upstream = current_upstream(data_home, desktop_id, local, directories)
                original = upstream.read_bytes().decode('utf-8') if upstream is not None and upstream.is_file() else ''
                fields = desktop_fields(original)
                if not fields or fields.get('Type', 'Application') != 'Application' or fields.get('Hidden', '').lower() == 'true' or fields.get('NoDisplay', '').lower() == 'true':
                    clear_managed_shadow(local, record)
                    del registry[desktop_id]
                    atomic_bytes(registry_path, (json.dumps(registry, indent=2, sort_keys=True) + '\n').encode())
                    print(f'Poistettu vanhentunut käynnistinkopio: {desktop_id}')
                    continue
                record['source'] = str(upstream)
                icon = themed_app_icon(desktop_id, fields, all_apps)
                if icon is None:
                    unsupported.append(desktop_id)
                    continue
        updated = replace_main_icon(original, icon).encode('utf-8')
        if local.is_file() and local.read_bytes() == updated:
            continue
        if updated == original.encode('utf-8') and record is None:
            continue
        backup = local.with_suffix('.desktop.before-icon-theme')
        if backup.is_symlink():
            raise ValueError(f'Varmuuskopio on symbolinen linkki: {backup}')
        had_local = local.exists()
        original_bytes = original.encode('utf-8')
        local.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(original_bytes)
        elif record is None and backup.read_bytes() != original_bytes:
            # Accept an older icon-only backup, never an unrelated/stale launcher.
            previous = backup.read_bytes().decode('utf-8')
            if replace_main_icon(previous, fields.get('Icon', '')) != original:
                raise ValueError(f'Aiempi varmuuskopio kuuluu eri käynnistimeen, säilytä tai siirrä se ensin: {backup}')
        if record is None:
            record = {'had_local': had_local, 'source': str(source), 'original_hash': digest(backup.read_bytes())}
        write_launcher(local, updated)
        record['modified_hash'] = digest(updated)
        registry[desktop_id] = record
        atomic_bytes(registry_path, (json.dumps(registry, indent=2, sort_keys=True) + '\n').encode())
        changed += 1
        print(f'Käynnistinkuvake: {desktop_id} → {icon}')
    if only and not found:
        raise ValueError('Ajanlaskut ja Sää -käynnistin puuttuu. Asenna ensin itse ohjelma.')
    print(f'Korjattu {changed} käynnistintä. Puuttuvia sovelluskuvia: {len(unsupported)}.')
    if unsupported:
        print('Puuttuvat: ' + ', '.join(unsupported))
        print('--all-app-icons käyttää näille sovelluksen luokan mukaista teemakuvaketta.')
    database = shutil.which('update-desktop-database')
    if changed and database:
        subprocess.run([database, str(data_home / 'applications')], check=True)
    return changed, unsupported


def restore_app_launchers(data_home):
    registry_path, registry = launcher_registry(data_home)
    # Validate every target before restoring any of them.
    for name, record in registry.items():
        local = data_home / 'applications' / name
        backup = local.with_suffix('.desktop.before-icon-theme')
        if local.is_symlink() or backup.is_symlink():
            raise ValueError(f'Käynnistin tai varmuuskopio on symbolinen linkki: {local}')
        if not local.is_file() or digest(local.read_bytes()) != record['modified_hash']:
            raise ValueError(f'Käynnistintä on muokattu, palautusta ei tehty: {local}')
        if not backup.is_file() or digest(backup.read_bytes()) != record['original_hash']:
            raise ValueError(f'Varmuuskopio puuttuu tai sitä on muokattu: {backup}')
        if record['had_local']:
            temporary = local.with_suffix('.desktop.icon-theme-tmp')
            if temporary.exists() or temporary.is_symlink():
                raise ValueError(f'Palautuksen väliaikaistiedosto on jo olemassa: {temporary}')
    for name, record in list(registry.items()):
        local = data_home / 'applications' / name
        backup = local.with_suffix('.desktop.before-icon-theme')
        if record['had_local']:
            write_launcher(local, backup.read_bytes())
        else:
            local.unlink()  # Reveal the current system launcher, not a stale copy.
        backup.unlink()
        del registry[name]
        atomic_bytes(registry_path, (json.dumps(registry, indent=2, sort_keys=True) + '\n').encode())
        print(f'Palautettu: {name}')


def launcher_override(data_home):
    fix_app_launchers(data_home, only={'ajanlaskut-ja-saa.desktop'})


def main():
    parser = argparse.ArgumentParser(description='Asenna Kupari-, Halla- ja Ubuntu-kuvaketeemat käyttäjälle ilman sudoa.')
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--theme', choices=THEMES, default='copper', help='käyttöön otettava teema (oletus: copper)')
    choice.add_argument('--match-widget', action='store_true', help='valitse ohjelman nykyinen yhteinen teema asetustiedostosta')
    parser.add_argument('--activate', action='store_true', help='vaihda GNOMEn kuvaketeema; ilman tätä vain asennetaan')
    parser.add_argument('--app-icon', action='store_true', help='korjaa ohjelman pääkäynnistin käyttämään teemakuvaketta, säilyttää varmuuskopion')
    parser.add_argument('--app-icons', action='store_true', help='korjaa tuettujen sovellusten käynnistinkuvakkeet, myös Snap/Flatpak')
    parser.add_argument('--all-app-icons', action='store_true', help='korjaa kaikki näkyvät käynnistimet; tuntemattomille luokan mukainen kuva')
    parser.add_argument('--restore-app-icons', action='store_true', help='palauta asentimen muuttamat käynnistimet, älä asenna teemoja')
    args = parser.parse_args()
    data_home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share').expanduser()
    if not data_home.is_absolute():
        parser.error('XDG_DATA_HOME on oltava absoluuttinen polku.')
    try:
        if args.restore_app_icons:
            if args.activate or args.app_icon or args.app_icons or args.all_app_icons:
                parser.error('--restore-app-icons on ajettava erillisenä komentona.')
            restore_app_launchers(data_home)
            return 0
        selected = match_widget(data_home) if args.match_widget else args.theme
        for name in THEMES.values():
            install_theme(ROOT / name, data_home / 'icons' / name)
        if args.app_icons or args.all_app_icons:
            fix_app_launchers(data_home, all_apps=args.all_app_icons)
        elif args.app_icon:
            launcher_override(data_home)
        if args.activate:
            activate(THEMES[selected])
        else:
            print(f'Valitse GNOME Tweaks → Ulkoasu → Kuvakkeet → {THEMES[selected]} tai käytä --activate.')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Virhe: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
