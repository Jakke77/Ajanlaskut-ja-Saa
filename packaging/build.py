#!/usr/bin/env python3
"""Rootless package and source-archive builder; no system or user mutations."""
import argparse
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from asaa import VERSION
from update_upgrade import atomic, atomic_json, digest, extract, version_number
DOCUMENTS=('README.md','ARCHITECTURE.md','CLOCK_WIDGET.md','UPDATES.md','LICENSE','THIRD_PARTY_NOTICES.md','VERIFICATION.md')

def files():
    for path in ROOT.rglob('*'):
        parts=path.relative_to(ROOT).parts
        if path.is_file() and not any(p in ('__pycache__','outputs','work','.git','.venv') for p in parts):
            yield path

def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    sources=list(files())
    with tempfile.TemporaryDirectory(prefix='ajanlaskut-paketti-') as directory:
        stage=Path(directory)
        app=stage/'usr/share/ajanlaskut-ja-saa'
        for source in sources:
            target=app/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target);target.chmod(0o644)
        doc=stage/'usr/share/doc/ajanlaskut-ja-saa';doc.mkdir(parents=True)
        for name in DOCUMENTS:shutil.copyfile(ROOT/name,doc/name)
        binary=stage/'usr/bin';binary.mkdir(parents=True)
        wrapper=binary/'ajanlaskut-ja-saa'
        wrapper.write_text('#!/bin/sh\nexec /usr/bin/python3 /usr/share/ajanlaskut-ja-saa/main.py "$@"\n')
        wrapper.chmod(0o755)
        desktop=stage/'usr/share/applications';desktop.mkdir(parents=True)
        (desktop/'ajanlaskut-ja-saa.desktop').write_text('[Desktop Entry]\nType=Application\nName=Ajanlaskut ja Sää\n'
            'Comment=Varjoaika, Tähtiaika, kalenterit ja sää yhdessä sovelluksessa\n'
            'Exec=ajanlaskut-ja-saa\nIcon=/usr/share/ajanlaskut-ja-saa/assets/icon.svg\n'
            'Terminal=false\nCategories=Office;Calendar;\nStartupNotify=true\n')
        control=stage/'DEBIAN';control.mkdir()
        (control/'control').write_text(f'Package: ajanlaskut-ja-saa\nVersion: {VERSION}\nArchitecture: all\n'
            'Maintainer: Jakke77 <Jakke77@users.noreply.github.com>\nSection: utils\nPriority: optional\n'
            'Depends: python3 (>= 3.10), python3-pyqt6 (>= 6.8), python3-pyqt6.qtmultimedia (>= 6.8)\n'
            'Recommends: python3-pyqt6.qtwebengine (>= 6.8), python3-gi, gir1.2-glib-2.0, xdg-desktop-portal, xdg-desktop-portal-gnome, geoclue-2.0\n'
            'Description: Finnish calendars and desktop weather\n'
            ' Varjoaika, Tahtiaika and Gregorian calendars with shared notes and reminders.\n'
            ' Weather forecasts, optional parallel calendars and eight desktop widgets.\n'
            ' A rotating clock uses copper, astral or Gregorian clock themes.\n')
        deb=output/f'ajanlaskut-ja-saa_{VERSION}_all.deb'
        subprocess.run(['dpkg-deb','--root-owner-group','--build',str(stage),str(deb)],check=True)
    archive=output/f'Ajanlaskut-ja-Saa-{VERSION}-lahdekoodi.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED) as stream:
        for source in sources:stream.write(source,Path('Ajanlaskut-ja-Saa')/source.relative_to(ROOT))
    checksum=output/'SHA256SUMS'
    checksum.write_text(''.join(sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n' for path in (deb,archive)))
    return deb,archive,checksum

def publish(channel):
    """Build and test an immutable release before atomically advertising it."""
    channel=Path(channel).resolve();packages=channel/'paketit';packages.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.julkaisu-',dir=packages) as directory:
        directory=Path(directory)
        deb,archive,checksum=build(directory/'artifacts')
        payload=directory/'qa-app';payload.mkdir()
        if extract(archive,payload)!=VERSION:raise ValueError('Julkaisun versio ei täsmää')
        import os
        environment=dict(os.environ,QT_QPA_PLATFORM='offscreen')
        log=directory/'artifacts'/'QA.log'
        try:
            with log.open('w') as output:
                subprocess.run(['/usr/bin/python3',str(payload/'main.py'),'--self-test'],env=environment,
                               stdout=output,stderr=subprocess.STDOUT,check=True,timeout=240)
        except subprocess.SubprocessError:
            import time
            failure=channel/'qa-failures'/f'{time.time_ns()}.log'
            atomic(failure,log.read_bytes())
            print('Julkaisu keskeytettiin. Testiloki:',failure,file=sys.stderr)
            raise
        archive_hash=digest(archive)
        index=dict(schema=1,app='ajanlaskut-ja-saa',version=VERSION,
                   archive=f'paketit/{VERSION}-{archive_hash[:16]}/{archive.name}',
                   sha256=archive_hash,size=archive.stat().st_size,qa='passed')
        old_index=channel/'latest.json'
        previous={}
        if old_index.exists():
            import json
            previous=json.loads(old_index.read_text())
            if (version_number(previous['version'])>version_number(VERSION)
                or previous['version']==VERSION and previous['sha256']!=archive_hash):
                raise ValueError('Julkaisu ei saa pienentää versiota tai korvata samaa versiota eri sisällöllä')
        target=channel/Path(index['archive']).parent
        if target.exists():
            if digest(target/archive.name)!=archive_hash:raise ValueError('Aiempi julkaisukansio ei täsmää')
        else:os.replace(directory/'artifacts',target)
        script=channel/'update-upgrade.py'
        source=ROOT/'packaging/update_upgrade.py'
        if script.exists() and previous.get('updater_sha256'):
            if digest(script)!=previous['updater_sha256']:raise ValueError('Päivitystiedostoa on muokattu, sitä ei korvattu')
        if script.exists() and not old_index.exists():raise ValueError('Kohteessa on muu päivitystiedosto, sitä ei korvattu')
        atomic(script,source.read_bytes(),0o755)
        index['updater_sha256']=digest(script)
        atomic_json(old_index,index)
        print('Julkaisu testattu ja paikallinen päivityskanava päivitetty:',VERSION)
        return old_index

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'outputs')
    parser.add_argument('--publish-channel',type=Path,help='Testaa paketti ja julkaise se paikalliseen päivityskansioon')
    args=parser.parse_args()
    if args.publish_channel:print(publish(args.publish_channel))
    else:
        for path in build(args.output):print(path)
