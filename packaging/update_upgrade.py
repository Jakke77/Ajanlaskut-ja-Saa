#!/usr/bin/env python3
"""Local, rootless release channel. Never calls apt, sudo or a network service."""
from __future__ import annotations
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from zipfile import ZipFile, BadZipFile

APP = 'ajanlaskut-ja-saa'
MARKER = '# Ajanlaskut ja Sää · paikallinen käyttäjäasennus\n'
REQUIRED = ('main.py','asaa/__init__.py','asaa/app.py','asaa/state.py','asaa/calendar.py','assets/icon.svg','LICENSE')
MAX_ARCHIVE = 60_000_000
MAX_EXPANDED = 120_000_000
MAX_FILES = 4096  # Five icon themes plus application, tests and bundled artwork.

def atomic(path, content, mode=0o600):
    path = Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(content.encode() if isinstance(content,str) else content)
            stream.flush();os.fsync(stream.fileno())
        os.chmod(temporary,mode);os.replace(temporary,path)
    finally:Path(temporary).unlink(missing_ok=True)

def atomic_json(path, data):atomic(path,json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def digest(path):
    hasher=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):hasher.update(chunk)
    return hasher.hexdigest()

def version_number(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{1,6}\.\d{1,6}\.\d{1,6}',value):
        raise ValueError('Virheellinen versionumero')
    return tuple(map(int,value.split('.')))

def desktop_quote(value):
    return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('%','%%').replace('$','\\$').replace('`','\\`')+'"'

def archive_version(path):
    tree=ast.parse(Path(path).read_text(encoding='utf-8'))
    for item in tree.body:
        if isinstance(item,ast.Assign) and any(isinstance(name,ast.Name) and name.id=='VERSION' for name in item.targets):
            if isinstance(item.value,ast.Constant):
                value=item.value.value;version_number(value);return value
    raise ValueError('Paketista puuttuu versionumero')

def extract(archive, stage):
    """No links, special files, traversal, duplicate paths or unbounded extraction."""
    with ZipFile(archive) as stream:
        entries=stream.infolist()
        if len(entries)>MAX_FILES or sum(item.file_size for item in entries)>MAX_EXPANDED:
            raise ValueError('Julkaisu on liian suuri')
        seen=set()
        for item in entries:
            path=PurePosixPath(item.filename)
            kind=stat.S_IFMT(item.external_attr>>16)
            if (path.is_absolute() or '..' in path.parts or '\\' in item.filename or '\x00' in item.filename
                or not path.parts or path.parts[0]!='Ajanlaskut-ja-Saa' or path in seen
                or kind not in (0,stat.S_IFREG,stat.S_IFDIR)):
                raise ValueError('Julkaisu sisältää turvattoman polun, linkin tai kaksoistiedoston')
            seen.add(path)
            relative=path.parts[1:]
            if any(part in ('work','outputs','.git','__pycache__') for part in relative):
                raise ValueError('Julkaisu sisältää työdataa')
            target=stage.joinpath(*relative)
            if item.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            if not relative:raise ValueError('Virheellinen julkaisujuuri')
            target.parent.mkdir(parents=True,exist_ok=True)
            with stream.open(item) as source,target.open('wb') as output:shutil.copyfileobj(source,output)
            target.chmod(0o644)
        if not all((stage/name).is_file() for name in REQUIRED):raise ValueError('Julkaisusta puuttuu ohjelman tiedostoja')
    return archive_version(stage/'asaa/__init__.py')

def dependency_check(python, stage):
    probe=('import sys; assert sys.version_info >= (3,10); sys.path.insert(0,sys.argv[1]); '
           'from PyQt6 import QtWidgets,QtNetwork,QtMultimedia; '
           'from PyQt6.QtCore import PYQT_VERSION_STR; '
           'assert tuple(map(int,PYQT_VERSION_STR.split(".")[:2])) >= (6,8); '
           'from asaa.calendar import Calendars; from asaa.almanac import SPECS; '
           'assert len(SPECS)>=1; Calendars()')
    try:subprocess.run([str(python),'-I','-c',probe,str(stage)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=30)
    except (OSError,subprocess.SubprocessError) as error:
        raise ValueError('Ohjelman riippuvuudet eivät lataudu. Nykyinen versio säilyy. '+str(error)) from error

class Updater:
    def __init__(self, channel, *, data_home=None, config_home=None, bin_dir=None, python='/usr/bin/python3'):
        self.channel=Path(channel).resolve()
        self.data=Path(data_home or os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share')).absolute()
        self.config=Path(config_home or os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')).absolute()
        self.binary=Path(bin_dir or Path.home()/'.local/bin').absolute()
        self.base=self.data/APP/'program'
        self.releases=self.base/'releases';self.current=self.base/'current'
        self.receipt=self.base/'installation.json';self.candidate=self.base/'candidate.json'
        self.python=Path(python).absolute()

    @contextmanager
    def locked(self):
        if os.geteuid()==0:raise ValueError('Aja oma päivityskomento ilman sudoa.')
        self.base.mkdir(parents=True,exist_ok=True,mode=0o700)
        with (self.base/'update.lock').open('a') as stream:
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('Toinen päivitys on jo käynnissä.') from None
            yield

    def load_release(self):
        index=self.channel/'latest.json'
        if index.stat().st_size>32_000:raise ValueError('Päivitysluettelo on liian suuri')
        release=json.loads(index.read_text(encoding='utf-8'))
        if release.get('schema')!=1 or release.get('app')!=APP or release.get('qa')!='passed':
            raise ValueError('Päivitysluettelo ei ole tämän ohjelman tarkistettu julkaisu')
        version_number(release.get('version'))
        relative=release.get('archive')
        if not isinstance(relative,str):raise ValueError('Virheellinen julkaisupolku')
        path=PurePosixPath(relative)
        if path.is_absolute() or '..' in path.parts or '\\' in relative or not relative.endswith('.zip'):
            raise ValueError('Julkaisun on oltava päivityskansion paikallinen ZIP-tiedosto')
        archive=(self.channel/relative).resolve(strict=True)
        if not archive.is_relative_to(self.channel):raise ValueError('Julkaisu ei saa poistua päivityskansiosta')
        if not re.fullmatch(r'[0-9a-f]{64}',str(release.get('sha256'))):raise ValueError('Virheellinen tarkiste')
        if type(release.get('size')) is not int or not 0<release['size']<=MAX_ARCHIVE:
            raise ValueError('Virheellinen julkaisukoko')
        if archive.stat().st_size!=release['size'] or digest(archive)!=release['sha256']:
            raise ValueError('Julkaisun tarkiste tai koko ei täsmää. Mitään ei asennettu.')
        return release,archive

    def installed(self, verify=True):
        if not self.receipt.exists():return None
        receipt=json.loads(self.receipt.read_text(encoding='utf-8'))
        if receipt.get('app')!=APP:raise ValueError('Tuntematon käyttäjäasennus')
        version_number(receipt.get('version'))
        target=self.release_path(receipt.get('current'),verify=verify)
        if not self.current.is_symlink() or self.current.resolve()!=target:
            raise ValueError('Ohjelman current-linkki ei vastaa asennustietoa')
        if receipt.get('previous') is not None:self.release_path(receipt['previous'],verify=False)
        if verify:
            marker=self.verify_target(target)
            if marker['version']!=receipt['version'] or marker['sha256']!=receipt.get('sha256'):
                raise ValueError('Asennustieto ei vastaa ohjelmaversiota')
        return receipt

    def release_path(self, relative, verify=True):
        if not isinstance(relative,str) or not re.fullmatch(r'releases/\d{1,6}\.\d{1,6}\.\d{1,6}-[0-9a-f]{16}',relative):
            raise ValueError('Virheellinen asennuskohde')
        target=(self.base/relative).resolve(strict=True)
        if target.parent!=self.releases.resolve() or not target.is_dir():raise ValueError('Asennuskohde poistuu ohjelman omasta kansiosta')
        if verify:self.verify_target(target)
        return target

    def verify_target(self, target):
        marker=json.loads((target/'.release.json').read_text())
        if marker.get('app')!=APP:raise ValueError('Tuntematon ohjelmakansio')
        version_number(marker.get('version'))
        files=marker.get('files')
        if not isinstance(files,dict) or not all(name in files for name in REQUIRED):raise ValueError('Vioittunut ohjelmakansio')
        for name, expected in files.items():
            relative=PurePosixPath(name)
            path=target.joinpath(*relative.parts)
            if (relative.is_absolute() or '..' in relative.parts or path.is_symlink()
                or not path.resolve().is_relative_to(target.resolve()) or digest(path)!=expected):
                raise ValueError('Ohjelmakansiota on muutettu tai se on vioittunut. Käyttäjän muutoksia ei korvattu.')
        if archive_version(target/'asaa/__init__.py')!=marker['version']:raise ValueError('Versionumero ei täsmää')
        return marker

    def update(self):
        with self.locked():
            release,_=self.load_release();self.installed();atomic_json(self.candidate,release)
            return release['version']

    def switch(self, relative, verify=True):
        target=self.release_path(relative,verify=verify)
        link=self.base/('.next-'+uuid.uuid4().hex)
        try:link.symlink_to(target.relative_to(self.base),target_is_directory=True);os.replace(link,self.current)
        finally:link.unlink(missing_ok=True)

    def launchers(self):
        command=self.binary/APP
        shell='#!/bin/sh\n'+MARKER+'exec '+shlex.quote(str(self.python))+' '+shlex.quote(str(self.current/'main.py'))+' "$@"\n'
        desktop=('[Desktop Entry]\n'+MARKER+'Type=Application\nName=Ajanlaskut ja Sää\n'
                 'Comment=Kalenterit ja sää · paikallinen päivityskanava\n'
                 'Exec='+desktop_quote(command)+'\nIcon='+str(self.current/'assets/icon.svg')+'\n'
                 'Terminal=false\nCategories=Office;Calendar;\nStartupNotify=true\n')
        files={command:(shell,0o755),self.data/'applications'/f'{APP}.desktop':(desktop,0o644)}
        startup=self.config/'autostart'/f'{APP}.desktop'
        if startup.exists():
            text=startup.read_text()
            if 'Name=Ajanlaskut ja Sää\n' not in text:raise ValueError('Tuntematonta kirjautumiskäynnistintä ei muutettu')
            lines=[('Exec='+desktop_quote(command)+' --widgets-only') if line.startswith('Exec=') else
                   ('Icon='+str(self.current/'assets/icon.svg')) if line.startswith('Icon=') else line for line in text.splitlines()]
            files[startup]=('\n'.join(lines)+'\n',0o644)
        return files

    def apply(self, relative, receipt, previous):
        files=self.launchers();snapshots={}
        for path in files:
            if path.is_symlink():raise ValueError('Symlinkkinä olevaa käynnistintä ei korvattu')
            snapshots[path]=(path.read_bytes(),stat.S_IMODE(path.stat().st_mode)) if path.exists() else None
            if snapshots[path] and path.parent==self.binary and MARKER.encode() not in snapshots[path][0]:
                raise ValueError('Samanniminen muu päätekomento on jo olemassa')
        if self.current.exists() and not self.current.is_symlink():raise ValueError('Olemassa olevaa current-kansiota ei korvattu')
        stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup=self.base/'backups'/stamp;backup.mkdir(parents=True,mode=0o700)
        state=self.data/APP/'state.json'
        if state.exists():shutil.copy2(state,backup/'state.json');(backup/'state.json').chmod(0o600)
        for index,(path,snapshot) in enumerate(snapshots.items()):
            if snapshot:atomic(backup/f'launcher-{index}',snapshot[0],snapshot[1])
        atomic_json(backup/'restore-map.json',{str(path):f'launcher-{i}' for i,path in enumerate(snapshots) if snapshots[path]})
        old_receipt=self.receipt.read_bytes() if self.receipt.exists() else None
        try:
            self.switch(relative)
            for path,(text,mode) in files.items():atomic(path,text,mode)
            atomic_json(self.receipt,receipt)
        except BaseException:
            if previous:self.switch(previous,verify=False)
            elif self.current.is_symlink():self.current.unlink()
            for path,snapshot in snapshots.items():
                if snapshot:atomic(path,*snapshot)
                else:path.unlink(missing_ok=True)
            if old_receipt is not None:atomic(self.receipt,old_receipt)
            else:self.receipt.unlink(missing_ok=True)
            raise
        return backup

    def upgrade(self):
        with self.locked():
            if not self.candidate.exists():raise ValueError('Suorita ensin codex-ajanlasku update.')
            release,archive=self.load_release()
            if json.loads(self.candidate.read_text())!=release:raise ValueError('Päivityslähde muuttui. Suorita update uudelleen.')
            previous=self.installed()
            if previous:
                comparison=version_number(release['version'])>version_number(previous['version'])
                if release['version']==previous['version']:
                    if release['sha256']!=previous['sha256']:raise ValueError('Samaa versionumeroa ei saa korvata eri paketilla')
                    return False,previous['version']
                if not comparison:raise ValueError('Vanhempaa versiota ei asenneta upgrade-komennolla. Käytä rollback-komentoa.')
            self.releases.mkdir(parents=True,exist_ok=True)
            relative='releases/'+release['version']+'-'+release['sha256'][:16]
            target=self.base/relative
            with tempfile.TemporaryDirectory(prefix='.unpack-',dir=self.releases) as temporary:
                stage=Path(temporary)/'app';stage.mkdir()
                if extract(archive,stage)!=release['version']:raise ValueError('Arkiston versio ei vastaa luetteloa')
                dependency_check(self.python,stage)
                files={path.relative_to(stage).as_posix():digest(path) for path in stage.rglob('*')
                       if path.is_file() and '__pycache__' not in path.parts}
                atomic_json(stage/'.release.json',dict(app=APP,version=release['version'],sha256=release['sha256'],files=files))
                if target.exists():
                    marker=self.verify_target(target)
                    if marker['version']!=release['version'] or marker.get('sha256')!=release['sha256']:
                        raise ValueError('Aiempi ohjelmakansio ei vastaa julkaistua pakettia')
                else:os.replace(stage,target)
            receipt=dict(app=APP,version=release['version'],sha256=release['sha256'],current=relative,
                         previous=previous['current'] if previous else None,python=str(self.python),channel=str(self.channel))
            self.apply(relative,receipt,previous['current'] if previous else None)
            return True,release['version']

    def rollback(self):
        with self.locked():
            installed=self.installed(verify=False)
            if not installed or not installed.get('previous'):raise ValueError('Edellistä käyttäjäasennuksen versiota ei ole.')
            target=self.release_path(installed['previous']);marker=self.verify_target(target)
            dependency_check(Path(installed['python']),target)
            self.python=Path(installed['python'])
            receipt=dict(installed,version=marker['version'],sha256=marker['sha256'],current=installed['previous'],previous=installed['current'])
            self.apply(receipt['current'],receipt,installed['current'])
            return receipt['version']

    def setup(self, script):
        with self.locked():
            script=Path(script).resolve(strict=True)
            command=self.binary/'codex-ajanlasku'
            if command.is_symlink() or (command.exists() and MARKER.encode() not in command.read_bytes()):
                raise ValueError('Samannimistä muuta komentoa ei korvattu')
            text='#!/bin/sh\n'+MARKER+'exec '+shlex.quote(str(self.python))+' '+shlex.quote(str(script))+' --channel-dir '+shlex.quote(str(self.channel))+' "$@"\n'
            atomic(command,text,0o755)
            return command

def main(argv=None):
    parser=argparse.ArgumentParser(description='Ajanlaskut ja Sää · paikallinen päivitys ilman sudoa')
    parser.add_argument('--channel-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('command',choices=['setup','update','upgrade','status','rollback','run'])
    parser.add_argument('app_args',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv);updater=Updater(args.channel_dir)
    try:
        if args.app_args and args.command!='run':raise ValueError('Vain run-komento ottaa ohjelman lisävalintoja.')
        if args.command=='setup':print('Oma komento asennettu:',updater.setup(Path(__file__)))
        elif args.command=='update':print('Paikallinen päivitysluettelo tarkistettu. Saatavilla:',updater.update())
        elif args.command=='upgrade':
            changed,version=updater.upgrade()
            print(('Päivitetty versioon ' if changed else 'Ohjelma on ajan tasalla: ')+version)
            if changed:print('Sulje Ajanlaskut ja Sää ja avaa se uudelleen: codex-ajanlasku run\nAsetukset ja merkinnät säilyvät. Edellinen ohjelmaversio jää palautettavaksi.')
        elif args.command=='rollback':
            print('Edellinen ohjelmaversio palautettu:',updater.rollback())
            print('Sulje ohjelma ja avaa se uudelleen. Nykyisiä merkintöjä ei palautettu taaksepäin.')
        elif args.command=='status':
            installed=updater.installed();print('Käyttäjäasennus:',installed['version'] if installed else 'ei vielä tehty')
            print('Päivityskansio:',updater.channel)
            if updater.candidate.exists():print('Viimeksi tarkistettu julkaisu:',json.loads(updater.candidate.read_text())['version'])
        elif args.command=='run':
            installed=updater.installed()
            if not installed:raise ValueError('Suorita ensin update ja upgrade.')
            os.execv(installed['python'],[installed['python'],str(updater.current/'main.py'),*args.app_args])
    except (OSError,ValueError,KeyError,TypeError,BadZipFile,SyntaxError,RuntimeError) as error:
        parser.exit(1,'Päivitys keskeytettiin: '+str(error)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
