"""Regressions for first installation and optional-content failures."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
from unittest import mock

from test_core import TemporaryLibrary
from fieldkit.books import start_kiwix
from fieldkit.common import write_json
from fieldkit.install import install, uninstall, service_text


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
