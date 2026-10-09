"""Updater failures must leave settings, desktop and active code untouched."""
import importlib.util
import json
from pathlib import Path
import stat
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

spec=importlib.util.spec_from_file_location('local_update_tests',Path(__file__).resolve().parents[1]/'packaging/update_upgrade.py')
updates=importlib.util.module_from_spec(spec);spec.loader.exec_module(updates)

class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory(prefix='ajanlaskut-updater-test-');self.root=Path(self.folder.name)
        self.channel=self.root/'kanava';self.channel.mkdir()
        self.manager=updates.Updater(self.channel,data_home=self.root/'data',config_home=self.root/'config',bin_dir=self.root/'bin')
        self.state=self.manager.data/updates.APP/'state.json';self.state.parent.mkdir(parents=True)
        self.state.write_text('{"notes":{"2026-10-08":"Oma merkintä"},"settings":{"provider":"windy"}}')
        self.state_bytes=self.state.read_bytes()
        self.probe=patch.object(updates,'dependency_check');self.probe.start()
    def tearDown(self):self.probe.stop();self.folder.cleanup()
    def release(self,version='1.2.1',extra=None,archive_version=None):
        path=self.channel/f'release-{version}.zip'
        with ZipFile(path,'w') as stream:
            for name in updates.REQUIRED:
                value=f'VERSION = {archive_version or version!r}\n' if name=='asaa/__init__.py' else 'test\n'
                stream.writestr('Ajanlaskut-ja-Saa/'+name,value)
            for name,value in extra or []:stream.writestr(name,value)
        release=dict(schema=1,app=updates.APP,version=version,archive=path.name,sha256=updates.digest(path),size=path.stat().st_size,qa='passed')
        updates.atomic_json(self.channel/'latest.json',release)
        return release,path
    def install(self,version='1.2.1'):
        self.release(version);self.manager.update();return self.manager.upgrade()
    def test_update_only_checks_no_program_or_desktop_change(self):
        self.release();self.assertEqual(self.manager.update(),'1.2.1')
        self.assertFalse(self.manager.current.exists());self.assertFalse((self.manager.data/'applications').exists())
        self.assertEqual(self.state.read_bytes(),self.state_bytes)
    def test_install_and_idempotent_upgrade(self):
        self.assertEqual(self.install(),(True,'1.2.1'));target=self.manager.current.resolve()
        self.assertEqual(self.manager.installed()['version'],'1.2.1')
        self.assertEqual(self.manager.upgrade(),(False,'1.2.1'));self.assertEqual(self.manager.current.resolve(),target)
        self.assertEqual(self.state.read_bytes(),self.state_bytes)
        self.assertEqual(len(list((self.manager.base/'backups').iterdir())),1)
        self.assertFalse((self.manager.config/'autostart').exists())
    def test_versions_and_rollback_preserve_new_notes(self):
        self.install('1.2.0');older=self.manager.current.resolve()
        self.install('1.2.1');newer=self.manager.current.resolve()
        self.state.write_text('Uusi merkintä pitää säilyttää myös palautuksessa')
        self.assertEqual(self.manager.rollback(),'1.2.0');self.assertEqual(self.manager.current.resolve(),older)
        self.assertEqual(self.state.read_text(),'Uusi merkintä pitää säilyttää myös palautuksessa')
        self.assertEqual(self.manager.rollback(),'1.2.1');self.assertEqual(self.manager.current.resolve(),newer)
    def test_rollback_can_recover_a_damaged_current_release(self):
        self.install('1.2.0');self.install('1.2.1')
        (self.manager.current/'main.py').write_text('Vaurioitunut tiedosto')
        self.assertEqual(self.manager.rollback(),'1.2.0');self.assertEqual(self.manager.installed()['version'],'1.2.0')
    def test_failed_checksum_never_changes_current(self):
        self.install('1.2.0');before=self.manager.installed()
        _,archive=self.release('1.2.1');archive.write_bytes(archive.read_bytes()+b'changed')
        with self.assertRaises(ValueError):self.manager.update()
        self.assertEqual(self.manager.installed(),before)
    def test_upgrade_verifies_again_after_update(self):
        self.release();self.manager.update();archive=self.channel/'release-1.2.1.zip'
        archive.write_bytes(archive.read_bytes()+b'changed')
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertFalse(self.manager.current.exists())
    def test_stale_update_requires_new_update(self):
        self.release('1.2.0');self.manager.update();self.release('1.2.1')
        with self.assertRaisesRegex(ValueError,'update uudelleen'):self.manager.upgrade()
    def test_missing_update_and_rollback_fail_without_mutation(self):
        with self.assertRaises(ValueError):self.manager.upgrade()
        with self.assertRaises(ValueError):self.manager.rollback()
        self.assertEqual(self.state.read_bytes(),self.state_bytes)
    def test_downgrade_and_same_version_replacement_are_rejected(self):
        self.install('1.2.1');before=self.manager.installed()
        self.release('1.2.0');self.manager.update()
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.release('1.2.1',extra=[('Ajanlaskut-ja-Saa/extra.txt','different')]);self.manager.update()
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertEqual(self.manager.installed(),before)
    def test_bad_archive_version_does_not_activate(self):
        self.release(archive_version='1.2.0');self.manager.update()
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertFalse(self.manager.current.exists())
    def test_dependency_failure_preserves_installed_version(self):
        self.install('1.2.0');before=self.manager.installed()
        self.release('1.2.1');self.manager.update()
        with patch.object(updates,'dependency_check',side_effect=ValueError('puuttuu')):
            with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertEqual(self.manager.installed(),before);self.assertEqual(self.state.read_bytes(),self.state_bytes)
    def test_path_traversal_absolute_path_and_symlink_rejected(self):
        for name in ['Ajanlaskut-ja-Saa/../../escaped','/tmp/escaped','Other/main.py','Ajanlaskut-ja-Saa/work/private.json']:
            self.release(extra=[(name,'bad')]);self.manager.update()
            with self.assertRaises(ValueError):self.manager.upgrade()
        _,archive=self.release()
        with ZipFile(archive,'a') as stream:
            link=ZipInfo('Ajanlaskut-ja-Saa/link');link.create_system=3;link.external_attr=(stat.S_IFLNK|0o777)<<16
            stream.writestr(link,'/etc/passwd')
        index=json.loads((self.channel/'latest.json').read_text());index.update(sha256=updates.digest(archive),size=archive.stat().st_size)
        updates.atomic_json(self.channel/'latest.json',index);self.manager.update()
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertFalse((self.root/'escaped').exists())
    def test_channel_cannot_use_external_files_or_unverified_release(self):
        release,archive=self.release()
        for change in ({'archive':'../elsewhere.zip'},{'app':'other'},{'qa':'not-tested'},{'size':True},{'version':'not-a-version'}):
            updates.atomic_json(self.channel/'latest.json',dict(release,**change))
            with self.assertRaises(ValueError):self.manager.update()
        external=self.root/'outside.zip';archive.rename(external);archive.symlink_to(external)
        updates.atomic_json(self.channel/'latest.json',release)
        with self.assertRaises(ValueError):self.manager.update()
    def test_transaction_failure_restores_launchers_pointer_and_receipt(self):
        self.install('1.2.0');before=self.manager.installed();old_target=self.manager.current.resolve()
        launcher=self.manager.binary/updates.APP;old_launcher=launcher.read_bytes()
        self.release('1.2.1');self.manager.update();real_atomic_json=updates.atomic_json
        def fail_once(path,data):
            if Path(path)==self.manager.receipt:raise OSError('Levy täynnä')
            return real_atomic_json(path,data)
        with patch.object(updates,'atomic_json',side_effect=fail_once):
            with self.assertRaises(OSError):self.manager.upgrade()
        self.assertEqual(self.manager.current.resolve(),old_target);self.assertEqual(launcher.read_bytes(),old_launcher)
        self.assertEqual(self.manager.installed(),before);self.assertEqual(self.state.read_bytes(),self.state_bytes)
    def test_existing_launcher_backed_up_and_autostart_stays_disabled(self):
        desktop=self.manager.data/'applications'/f'{updates.APP}.desktop';desktop.parent.mkdir()
        desktop.write_text('Vanha käyttäjän käynnistin')
        startup=self.manager.config/'autostart'/f'{updates.APP}.desktop';startup.parent.mkdir(parents=True)
        startup.write_text('[Desktop Entry]\nName=Ajanlaskut ja Sää\nExec=old\nX-GNOME-Autostart-enabled=false\n')
        self.install()
        self.assertIn('X-GNOME-Autostart-enabled=false',startup.read_text())
        self.assertIn('current',(self.manager.binary/updates.APP).read_text())
        backup=next((self.manager.base/'backups').iterdir())
        restore=json.loads((backup/'restore-map.json').read_text())
        self.assertEqual((backup/restore[str(desktop)]).read_text(),'Vanha käyttäjän käynnistin')
        self.assertEqual((backup/'state.json').stat().st_mode&0o777,0o600)
    def test_unknown_command_or_regular_current_directory_not_overwritten(self):
        self.manager.binary.mkdir();command=self.manager.binary/updates.APP;command.write_text('Muu komento')
        self.release();self.manager.update()
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertEqual(command.read_text(),'Muu komento')
        command.unlink();self.manager.current.mkdir()
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertTrue(self.manager.current.is_dir())
    def test_setup_quotes_paths_idempotent_and_refuses_other_command(self):
        script=self.channel/'update upgrade.py';script.write_text('print("test")')
        path=self.manager.setup(script);self.assertEqual(path.stat().st_mode&0o777,0o755)
        self.assertIn("'",path.read_text());self.manager.setup(script)
        path.write_text('Muu samanniminen komento')
        with self.assertRaises(ValueError):self.manager.setup(script)
    def test_sudo_rejected_without_creating_program_directories(self):
        with patch.object(updates.os,'geteuid',return_value=0):
            with self.assertRaises(ValueError):self.manager.update()
        self.assertFalse(self.manager.base.exists())
    def test_managed_startup_uses_stable_current_path(self):
        from asaa import startup
        self.install()
        frozen=self.manager.current.resolve()
        with patch.object(startup,'ROOT',frozen):
            self.assertEqual(startup.launcher_root(),self.manager.current)
            text=startup.entry(widgets_only=True)
            self.assertIn(str(self.manager.current/'main.py'),text)
            self.assertNotIn(str(frozen),text)
            self.assertIn('--widgets-only',text)
        with patch.object(startup,'ROOT',self.root/'developer-source'):
            self.assertEqual(startup.launcher_root(),self.root/'developer-source')
    def test_existing_release_metadata_must_match_candidate(self):
        self.install('1.2.0');self.install('1.2.1');self.manager.rollback()
        target=next(self.manager.releases.glob('1.2.1-*'))
        marker=json.loads((target/'.release.json').read_text());marker['sha256']='f'*64
        updates.atomic_json(target/'.release.json',marker)
        with self.assertRaises(ValueError):self.manager.upgrade()
        self.assertEqual(self.manager.installed()['version'],'1.2.0')
    def test_failed_publication_leaves_previous_channel_and_helper(self):
        _,archive=self.release()
        with patch.dict(sys.modules,{'update_upgrade':updates}):
            location=Path(__file__).resolve().parents[1]/'packaging/build.py'
            build_spec=importlib.util.spec_from_file_location('local_publish_tests',location)
            builder=importlib.util.module_from_spec(build_spec);build_spec.loader.exec_module(builder)
        old=b'{"version":"1.2.0","sha256":"old"}\n'
        (self.channel/'latest.json').write_bytes(old)
        helper=self.channel/'update-upgrade.py';helper.write_text('previous updater')
        def package(output):
            output.mkdir();deb=output/'test.deb';deb.write_bytes(b'fake-deb')
            result=output/archive.name;shutil.copyfile(archive,result)
            checksum=output/'SHA256SUMS';checksum.write_text('test')
            return deb,result,checksum
        with patch.object(builder,'VERSION','1.2.1'),patch.object(builder,'build',side_effect=package),patch.object(builder.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'Qt test')):
            with self.assertRaises(subprocess.CalledProcessError):builder.publish(self.channel)
        self.assertEqual((self.channel/'latest.json').read_bytes(),old)
        self.assertEqual(helper.read_text(),'previous updater')
        self.assertTrue(list((self.channel/'qa-failures').glob('*.log')))
        self.assertEqual(list((self.channel/'paketit').iterdir()),[])
