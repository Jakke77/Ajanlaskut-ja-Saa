#!/usr/bin/env python3
"""Build a Windows x64 ZIP on Linux or Windows from verified cached downloads.

Downloads are provisioned separately. This builder never downloads dependencies,
executes package installers, or includes personal application data.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from asaa import VERSION
WINDOWS = ROOT / 'packaging/windows'


def verified_downloads(cache):
    manifest = json.loads((WINDOWS / 'downloads.json').read_text(encoding='utf-8'))
    result = []
    for record in manifest['files']:
        path = cache / record['name']
        if sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Latauksen tarkiste ei täsmää: ' + path.name)
        result.append(path)
    return result


def unpack(archive, destination):
    with ZipFile(archive) as stream:
        for member in stream.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Paketin polku poistuu kohdekansiosta.')
        stream.extractall(destination)


def source_files():
    yield ROOT / 'main.py'
    yield ROOT / 'packaging/build_windows.py'
    for folder in ('asaa', 'vendor', 'tests', 'packaging/windows', 'assets/wallpapers'):
        for source in sorted((ROOT / folder).rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc':
                yield source
    for name in ('icon.svg', 'calendar-names.json', 'huuhkaja.wav'):
        yield ROOT / 'assets' / name
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'WINDOWS.md'):
        yield ROOT / name


def build(output, cache, zig):
    downloads = verified_downloads(cache)
    output.mkdir(parents=True, exist_ok=True)
    name = f'Ajanlaskut-ja-Saa-{VERSION}-Windows10-x64'
    stage = output / name
    if stage.exists():
        raise ValueError('Kohdekansio on jo olemassa: ' + str(stage))
    stage.mkdir()
    for source in source_files():
        target = stage / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
    runtime = stage / 'runtime'; runtime.mkdir()
    packages = runtime / 'Lib/site-packages'; packages.mkdir(parents=True)
    for path in downloads:
        unpack(path, packages if path.suffix == '.whl' else runtime)
    (runtime / 'python312._pth').write_text(
        'python312.zip\n.\nLib/site-packages\n..\n../vendor\nimport site\n', encoding='utf-8')
    # Keep licence notices beside every binary distribution, including wheel metadata.
    shutil.copyfile(WINDOWS / 'downloads.json', stage / 'DEPENDENCIES.json')
    resource = output / 'launcher.res'
    subprocess.run([str(zig), 'rc', '/fo', str(resource), 'launcher.rc'], cwd=WINDOWS, check=True)
    subprocess.run([str(zig), 'cc', '-target', 'x86_64-windows-gnu', '-Os', '-s', '-municode', '-Wl,--subsystem,windows',
                    str(WINDOWS / 'launcher.c'), str(resource), '-o', str(stage / 'Ajanlaskut-ja-Saa.exe'),
                    '-luser32'], check=True)
    resource.unlink()
    for filename, command in {
        'Vain-widgetit.cmd': 'start "" "%~dp0Ajanlaskut-ja-Saa.exe" --widgets-only',
        'Tarkista-toiminta.cmd': '"%~dp0runtime\\python.exe" "%~dp0main.py" --self-test\r\npause',
        'Tarkista-verkkoyhteys.cmd': '"%~dp0runtime\\python.exe" -m asaa.weather.network_test\r\npause',
        'Luo-pikakuvakkeet.cmd': 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Luo-pikakuvakkeet.ps1"\r\npause',
    }.items():
        (stage / filename).write_bytes(('@echo off\r\n' + command + '\r\n').encode('utf-8'))
    shutil.copyfile(WINDOWS / 'Luo-pikakuvakkeet.ps1', stage / 'Luo-pikakuvakkeet.ps1')
    (stage / 'LUEMINUT.txt').write_text((ROOT / 'WINDOWS.md').read_text(encoding='utf-8'), encoding='utf-8-sig')
    archive = output / (name + '.zip')
    with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=6) as stream:
        for path in sorted(stage.rglob('*')):
            if path.is_file(): stream.write(path, Path(name) / path.relative_to(stage))
    sums = output / 'SHA256SUMS'
    sums.write_text(sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n', encoding='ascii')
    print(archive); print(sums)
    return stage, archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--zig', required=True, type=Path)
    args = parser.parse_args()
    build(args.output.resolve(), args.cache.resolve(), args.zig.resolve())
