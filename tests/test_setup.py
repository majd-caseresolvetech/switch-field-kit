"""Regressions for first installation and optional-content failures."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import importlib.util
from unittest import mock

from test_core import TemporaryLibrary
from fieldkit.books import start_kiwix
from fieldkit.common import APP, config, write_json
from fieldkit.install import install, uninstall, service_text, open_library, wait_books
from fieldkit.desktop import desktop_dir, desktop_quote, set_autostart


class SetupTests(TemporaryLibrary):
    def setUp(self):
        super().setUp()
        self.home = self.root/'User with spaces'
        self.home.mkdir()
        self.args = argparse.Namespace(no_system=True, no_service=True, guides=False,
                                       data=str(self.root/'data'), port=18095)
        self.patches = [mock.patch('pathlib.Path.home', return_value=self.home),
                        mock.patch('platform.system', return_value='Linux'),
                        mock.patch('os.geteuid', return_value=1000),
                        mock.patch.dict(os.environ, {'XDG_DATA_HOME':str(self.home/'.local/share'),
                                                     'XDG_CONFIG_HOME':str(self.home/'.config')})]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        super().tearDown()

    def test_launcher_uses_the_installed_config_without_setup_environment(self):
        install(self.args)
        env = dict(os.environ)
        env.pop('FIELDKIT_CONFIG', None)
        env.pop('FIELDKIT_DATA', None)
        raw = subprocess.check_output([str(self.home/'.local/bin/fieldkit'), 'doctor'], env=env)
        self.assertEqual(json.loads(raw.decode())['data'], str((self.root/'data').resolve()))
        unit = service_text(self.home/'.local/share/switch-field-kit/app')
        self.assertIn('Environment="FIELDKIT_CONFIG='+str((self.root/'config.json').resolve())+'"', unit)

    def test_explicit_guides_fail_before_install_if_pdf_tools_missing(self):
        self.args.guides = True
        with mock.patch('shutil.which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'PDF tools are missing'):
                install(self.args)
        self.assertFalse((self.home/'.local/share/switch-field-kit/app').exists())

    def test_default_setup_skips_guides_with_clear_recovery_if_tools_missing(self):
        self.args.guides = None
        log = io.StringIO()
        with mock.patch('shutil.which', return_value=None), mock.patch('fieldkit.content.install_guides') as guides, contextlib.redirect_stdout(log):
            install(self.args)
        guides.assert_not_called()
        self.assertIn('sudo apt install poppler-utils', log.getvalue())
        self.assertIn('~/.local/bin/fieldkit serve', log.getvalue())

    def test_failed_download_keeps_reader_and_explains_retry(self):
        self.args.guides = True
        with mock.patch('shutil.which', return_value='/test/tool'), mock.patch('fieldkit.content.install_guides', side_effect=RuntimeError('Publisher unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'No reinstall is needed'):
                install(self.args)
        self.assertTrue((self.home/'.local/share/switch-field-kit/app/fieldkit/server.py').exists())

    def test_library_inside_app_is_rejected_and_not_deleted_on_uninstall(self):
        danger = self.home/'.local/share/switch-field-kit/app/library'
        danger.mkdir(parents=True)
        book = danger/'keep.txt'
        book.write_text('saved book')
        self.args.data = str(danger)
        with self.assertRaisesRegex(ValueError, 'outside the app'):
            install(self.args)
        with mock.patch.dict(os.environ, {'FIELDKIT_DATA':str(danger)}):
            with self.assertRaisesRegex(ValueError, 'outside the app'):
                uninstall()
        self.assertEqual(book.read_text(), 'saved book')

    def test_service_failure_is_not_reported_as_running(self):
        self.args.no_service = False
        with mock.patch('shutil.which', return_value='/test/tool'), mock.patch('subprocess.call', return_value=0), mock.patch('subprocess.check_call'), mock.patch('fieldkit.install.reader_ready', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'reader did not start'):
                install(self.args)

    def test_missing_kiwix_does_not_stop_the_reader(self):
        data = self.root/'data'
        data.mkdir()
        book = data/'sample.zim'
        book.write_bytes(b'ZIM\x04')
        write_json(data/'books.json', [{'path':str(book)}])
        self.assertIsNone(start_kiwix({'data':str(data), 'kiwix_binary':str(data/'missing-program')}, 18096))

    def test_first_service_install_opens_at_login_and_keeps_other_autostarts(self):
        self.args.no_service = False
        other = self.home/'.config/autostart/other-app.desktop'
        other.parent.mkdir(parents=True)
        other.write_text('existing app')
        with mock.patch('shutil.which', return_value='/test/tool'), mock.patch('subprocess.call', return_value=0), mock.patch('subprocess.check_call'), mock.patch('subprocess.run'), mock.patch('fieldkit.install.reader_ready', return_value=True):
            install(self.args)
        startup = (other.parent/'switch-field-kit.desktop').read_text()
        self.assertIn('Hidden=false', startup)
        self.assertIn('X-GNOME-Autostart-enabled=true', startup)
        self.assertIn('StartupWMClass=SwitchFieldKit', startup)
        self.assertTrue((self.home/'Desktop/Switch Field Kit.desktop').is_file())
        self.assertEqual(other.read_text(), 'existing app')

    def test_login_choice_survives_update_and_uninstall_removes_shortcuts(self):
        install(self.args)
        with mock.patch('subprocess.run'):
            set_autostart(False)
        self.args.no_service = False
        with mock.patch('shutil.which', return_value='/test/tool'), mock.patch('subprocess.call', return_value=0), mock.patch('subprocess.check_call'), mock.patch('subprocess.run'), mock.patch('fieldkit.install.reader_ready', return_value=True):
            install(self.args)
        self.assertFalse(config()['autostart'])
        startup = self.home/'.config/autostart/switch-field-kit.desktop'
        self.assertIn('Hidden=true', startup.read_text())
        original = self.home/'Desktop/Offline Library.desktop'
        original.write_text('original stays')
        with mock.patch('fieldkit.install.ask', return_value=True), mock.patch('subprocess.run'):
            uninstall()
        self.assertFalse(startup.exists())
        self.assertFalse((self.home/'Desktop/Switch Field Kit.desktop').exists())
        self.assertEqual(original.read_text(), 'original stays')

    def test_manual_install_cannot_claim_to_autostart_without_service(self):
        self.args.autostart = True
        with self.assertRaisesRegex(ValueError, 'requires the login service'):
            install(self.args)
        self.assertFalse((self.home/'.local/bin/fieldkit').exists())

    def test_browser_and_desktop_use_separate_fieldkit_window_identity(self):
        with mock.patch('shutil.which', return_value='/test/browser'), mock.patch('subprocess.run'), mock.patch('subprocess.Popen') as launch, mock.patch('fieldkit.install.reader_ready', return_value=True):
            open_library()
        command = launch.call_args[0][0]
        self.assertIn('--class=SwitchFieldKit', command)
        self.assertIn('--app=http://127.0.0.1:8095/', command)

    def test_desktop_paths_respect_localisation_and_disabled_desktop(self):
        dirs = self.home/'.config/user-dirs.dirs'
        dirs.parent.mkdir(parents=True, exist_ok=True)
        dirs.write_text('XDG_DESKTOP_DIR="$HOME/Bureau"\n')
        self.assertEqual(desktop_dir(), self.home/'Bureau')
        dirs.write_text('XDG_DESKTOP_DIR="$HOME/"\n')
        self.assertIsNone(desktop_dir())
        self.assertEqual(desktop_quote('a\\b$c%d'), '"a'+'\\'*4+'b'+'\\'*2+'$c%%d"')
        with self.assertRaises(ValueError):
            desktop_quote('bad\npath')

    def test_shared_books_wait_for_actual_files_and_explain_missing_storage(self):
        path = self.root/'mounted/book.zim'
        write_json(self.root/'data/books.json', [{'path':str(path), 'title':'Shared book'}])
        with self.assertRaisesRegex(RuntimeError, 'Shared book'):
            wait_books(timeout=0)
        path.parent.mkdir()
        path.write_bytes(b'ZIM\x04')
        wait_books(timeout=0)

    def original_helper(self):
        spec = importlib.util.spec_from_file_location('keep_original_library', str(APP/'scripts/keep_original_library.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_original_helper_preserves_files_and_keeps_original_launch_independent(self):
        launcher = self.home/'.local/bin/offline-library'
        launcher.parent.mkdir(parents=True)
        original = "import subprocess\n# switch-offline-library.service switch-offline-browser\nsubprocess.Popen(['chromium-browser','--app=http://127.0.0.1:8080/'])\n"
        launcher.write_text(original)
        (launcher.parent/'fieldkit').write_text('installed')
        helper = self.original_helper()
        with mock.patch('shutil.which', return_value=None):
            backup = helper.keep_original()
            helper.keep_original()
        self.assertEqual((backup/'0-offline-library').read_text(), original)
        self.assertEqual(launcher.read_text().count('--class=OriginalOfflineLibrary'), 1)
        desktop = (self.home/'Desktop/Offline Library.desktop').read_text()
        self.assertIn('StartupWMClass=OriginalOfflineLibrary', desktop)
        self.assertIn(desktop_quote(launcher), desktop)
        self.assertNotIn('fieldkit" open', desktop)
        self.assertIn('Hidden=true', (self.home/'.config/autostart/offline-library.desktop').read_text())

    def test_original_helper_refuses_absent_or_unrecognised_apps_before_writing(self):
        helper = self.original_helper()
        with self.assertRaisesRegex(RuntimeError, 'No original Offline Library'):
            helper.keep_original()
        launcher = self.home/'.local/bin/offline-library'
        launcher.parent.mkdir(parents=True)
        launcher.write_text('unrelated application')
        (launcher.parent/'fieldkit').write_text('installed')
        with self.assertRaisesRegex(RuntimeError, 'left unchanged'):
            helper.keep_original()
        self.assertEqual(launcher.read_text(), 'unrelated application')
        self.assertFalse((self.home/'.config/autostart/offline-library.desktop').exists())

    def test_shared_original_dependency_requires_existing_service_and_preserves_it(self):
        launcher = self.home/'.local/bin/offline-library'
        launcher.parent.mkdir(parents=True)
        original = "import subprocess\n# switch-offline-library.service switch-offline-browser\nsubprocess.Popen(['chromium-browser','--app=http://127.0.0.1:8080/'])\n"
        launcher.write_text(original)
        (launcher.parent/'fieldkit').write_text('installed')
        helper = self.original_helper()
        with self.assertRaisesRegex(RuntimeError, 'service is missing'):
            helper.keep_original(shared_books=True)
        self.assertEqual(launcher.read_text(), original)
        unit = self.home/'.config/systemd/user/switch-offline-library.service'
        unit.parent.mkdir(parents=True)
        unit.write_text('existing service')
        with mock.patch('shutil.which', return_value=None), mock.patch('subprocess.check_call') as commands:
            helper.keep_original(shared_books=True)
        dependency = unit.parent/'switch-field-kit.service.d/original-library.conf'
        self.assertIn('Requires=switch-offline-library.service', dependency.read_text())
        self.assertIn(' wait-books', dependency.read_text())
        self.assertEqual(unit.read_text(), 'existing service')
        self.assertEqual(commands.call_args[0][0], ['systemctl','--user','restart','switch-field-kit.service'])
