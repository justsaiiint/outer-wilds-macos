import io
import json
from pathlib import Path
import sys
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import owmac


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'prefix/drive_c/users/Someone/AppData/LocalLow/Mobius Digital/Outer Wilds'
        self.profile = self.base / 'SteamSaves/A different profile'
        self.profile.mkdir(parents=True)
        self.graphics = self.profile / 'graphics.owsett'
        self.original = {'fullScreen': True, 'textureQuality': 0, 'shadowQuality': 3,
                         'customFutureSetting': {'keep': True}, 'displayResWidth': 1920,
                         'displayResHeight': 1080}
        self.graphics.write_text(json.dumps(self.original))
        self.save = self.profile / 'data.owprofile'
        self.save.write_bytes(b'private save progress\x00\xff')
        (self.base / 'secretsettings.txt').write_text('// PhysicsRate=60\nPhysicsRate=120\nMouseSmoothTimeBuffer=0\n')

    @patch('owmac.game_running', return_value=False)
    def test_changes_only_display_and_performance_settings(self, _):
        owmac.configure(self.root, 60, 3024, 1964)
        current = json.loads(self.graphics.read_text())
        for key in ['textureQuality', 'shadowQuality', 'customFutureSetting']:
            self.assertEqual(current[key], self.original[key])
        self.assertFalse(current['fullScreen'])
        self.assertEqual(self.save.read_bytes(), b'private save progress\x00\xff')
        secret = (self.base / 'secretsettings.txt').read_text()
        self.assertIn('MouseSmoothTimeBuffer=0', secret)
        self.assertIn('\nPhysicsRate=60\n', secret)
        self.assertIn('VSyncCount=0', secret)
        originals = list((self.root / 'backups').glob('**/graphics.owsett'))
        self.assertEqual(len(originals), 1)
        self.assertEqual(json.loads(originals[0].read_text()), self.original)
        count = len(list((self.root / 'backups').glob('**/*')))
        owmac.configure(self.root, 60, 3024, 1964)
        self.assertEqual(count, len(list((self.root / 'backups').glob('**/*'))))

    @patch('owmac.game_running', return_value=True)
    def test_refuses_live_game_without_writes(self, _):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaises(RuntimeError):
            owmac.configure(self.root, 60, 3024, 1964)
        after = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_unmarked_installation_is_refused(self):
        with self.assertRaises(RuntimeError):
            owmac.require_install(self.root)

    @patch('owmac.game_running', return_value=False)
    def test_external_secret_settings_are_not_read_or_copied(self, _):
        with tempfile.TemporaryDirectory() as other:
            external = Path(other) / 'private.txt'
            external.write_text('PRIVATE CONTENT')
            secret = self.base / 'secretsettings.txt'
            secret.unlink()
            secret.symlink_to(external)
            with self.assertRaises(RuntimeError):
                owmac.configure(self.root, 60, 3024, 1964)
            self.assertEqual(external.read_text(), 'PRIVATE CONTENT')
            self.assertFalse(list((self.root / 'backups').glob('**/secretsettings.txt')))

    @patch('owmac.game_running', return_value=False)
    def test_external_renderer_config_is_not_read_or_copied(self, _):
        with tempfile.TemporaryDirectory() as other:
            external = Path(other) / 'private.txt'
            external.write_text('PRIVATE CONTENT')
            (self.root / 'dxmt.conf').symlink_to(external)
            with self.assertRaises(RuntimeError):
                owmac.configure(self.root, 60, 3024, 1964)
            self.assertFalse((self.root / 'backups').exists())

    @patch('owmac.game_running', return_value=False)
    def test_profile_symlink_cannot_write_outside_prefix(self, _):
        outside = self.root / 'outside'
        outside.mkdir()
        target = outside / 'graphics.owsett'
        target.write_text(json.dumps(self.original))
        self.graphics.unlink()
        self.graphics.symlink_to(target)
        with self.assertRaises(RuntimeError):
            owmac.configure(self.root, 60, 3024, 1964)
        self.assertEqual(json.loads(target.read_text()), self.original)


class ArchiveTests(unittest.TestCase):
    def test_selection_excludes_proprietary_renderer_and_wrapper(self):
        base = 'Template-1.0.18.app/Contents/Frameworks/'
        for name in ['renderer/d3dmetal/foo', 'SikarugirSdk.framework/binary', '../secret']:
            self.assertIsNone(owmac.template_member(base + name))
        self.assertEqual(owmac.template_member(base + 'renderer/dxmt/LICENSE'), 'dxmt/LICENSE')
        self.assertEqual(owmac.template_member(base + 'libtest.dylib'), 'Frameworks/libtest.dylib')

    def test_traversal_and_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, info in [('traversal', tarfile.TarInfo('../escape')), ('symlink', tarfile.TarInfo('link'))]:
                if label == 'symlink':
                    info.type = tarfile.SYMTYPE
                    info.linkname = '../../escape'
                archive = root / (label + '.tar.xz')
                with tarfile.open(archive, 'w:xz') as bundle:
                    bundle.addfile(info)
                with self.assertRaises(RuntimeError):
                    owmac.extract_selected(archive, root / label, lambda name: name)
                self.assertFalse((root.parent / 'escape').exists())

    def test_valid_relative_symlinks_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'valid.tar.xz'
            with tarfile.open(archive, 'w:xz') as bundle:
                file = tarfile.TarInfo('lib/a')
                file.size = 4
                bundle.addfile(file, io.BytesIO(b'test'))
                link = tarfile.TarInfo('lib/b')
                link.type = tarfile.SYMTYPE
                link.linkname = 'a'
                bundle.addfile(link)
            owmac.extract_selected(archive, root / 'out', lambda name: name)
            self.assertEqual((root / 'out/lib/b').read_bytes(), b'test')

    def test_bad_cached_download_is_never_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'file').write_bytes(b'bad')
            with patch('urllib.request.urlopen') as request:
                with self.assertRaises(RuntimeError):
                    owmac.download({'filename': 'file', 'sha256': '0' * 64, 'url': 'https://example.com/file'}, cache)
                request.assert_not_called()


class EnvironmentTests(unittest.TestCase):
    def test_generated_launcher_falls_back_from_removed_python(self):
        with tempfile.TemporaryDirectory(prefix="owmac space '") as tmp:
            root = Path(tmp) / 'support'
            (root / 'logs').mkdir(parents=True)
            (root / 'launcher').mkdir()
            (root / 'launcher/owmac.py').write_text('print("LAUNCH_OK")\n')
            app = Path(tmp) / 'test.app'
            with patch('sys.executable', '/nonexistent/python3'):
                owmac.create_app(root, app)
            subprocess.run(['/bin/bash', str(app / 'Contents/MacOS/Launch')], check=True)
            self.assertIn('LAUNCH_OK', (root / 'logs/launcher.log').read_text())

    def test_parent_wine_environment_cannot_select_a_different_prefix(self):
        with patch.dict('os.environ', {'WINEPREFIX': '/wrong', 'WINEDLLOVERRIDES': 'dxgi=n', 'WINEARCH': 'win32', 'DXMT_CONFIG_FILE': '/wrong'}):
            env = owmac.wine_env(Path('/test'))
        self.assertEqual(env['WINEPREFIX'], '/test/prefix')
        self.assertNotIn('WINEARCH', env)
        self.assertEqual(env['WINEDLLOVERRIDES'], 'winemenubuilder.exe=d')
        self.assertEqual(env['DXMT_CONFIG_FILE'], 'Z:/test/dxmt.conf')


if __name__ == '__main__':
    unittest.main()
