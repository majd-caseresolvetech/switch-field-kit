import contextlib
import gzip
import http.client
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
import threading
import unittest
import argparse
from unittest import mock

from fieldkit.common import APP, atomic, catalogue, config, digest, write_json
from fieldkit.books import add_book
from fieldkit.install import service_text, unit_quote
from fieldkit.maps import map_info
from fieldkit.server import Handler, Server

class TemporaryLibrary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fieldkit-test-')
        self.root = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {'FIELDKIT_DATA':str(self.root/'data'), 'FIELDKIT_CONFIG':str(self.root/'config.json')})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

class CoreTests(TemporaryLibrary):
    def test_install_and_remove_preserve_content_and_other_files(self):
        from fieldkit.install import install, uninstall
        home=self.root/'Account With Spaces'
        home.mkdir()
        (home/'keep.txt').write_text('existing file')
        library=self.root/'data';library.mkdir();(library/'keep-book.txt').write_text('existing book')
        env={'XDG_DATA_HOME':str(home/'.local/share'),'XDG_CONFIG_HOME':str(home/'.config')}
        args=argparse.Namespace(no_system=True,no_service=True,guides=False,data=str(library),port=18095)
        with mock.patch.dict(os.environ,env),mock.patch('pathlib.Path.home',return_value=home),mock.patch('platform.system',return_value='Linux'),mock.patch('os.geteuid',return_value=1000):
            install(args)
            target=home/'.local/share/switch-field-kit/app'
            self.assertTrue((target/'fieldkit/server.py').is_file())
            self.assertTrue((home/'.local/bin/fieldkit').is_file())
            install(args)
            self.assertTrue((home/'.local/share/switch-field-kit/previous/fieldkit/server.py').is_file())
            with mock.patch('fieldkit.install.ask',return_value=True),mock.patch('subprocess.run'):
                uninstall()
            self.assertFalse(target.exists())
        self.assertEqual((library/'keep-book.txt').read_text(),'existing book')
        self.assertEqual((home/'keep.txt').read_text(),'existing file')

    def test_catalogue_has_originals_and_valid_sections(self):
        docs = catalogue()
        self.assertEqual(len(docs), 27)
        self.assertEqual(sum(d['pages'] for d in docs), 466)
        self.assertEqual(len({d['id'] for d in docs}), 27)
        for d in docs:
            self.assertRegex(d['id'], r'^[a-z0-9-]+$')
            self.assertTrue(d['url'].startswith('https://'))
            self.assertRegex(d['sha256'], r'^[a-f0-9]{64}$')
            self.assertTrue(1 <= d['start'] <= d['pages'])
            self.assertEqual(sorted(s[0] for s in d['sections']), [s[0] for s in d['sections']])
            for page, title in d['sections']:
                self.assertTrue(1 <= page <= d['pages'])
                self.assertTrue(title)

    def test_atomic_overwrite_and_config_port_validation(self):
        p = self.root/'nested/file'
        atomic(p, b'first')
        atomic(p, b'second')
        self.assertEqual(p.read_bytes(), b'second')
        write_json(self.root/'config.json', {'port':80})
        with self.assertRaises(ValueError):
            config()

    def test_systemd_quoting_for_spaces_and_percent(self):
        unit = service_text(Path('/home/example user/100% library/app'))
        self.assertIn('"/home/example user/100%% library/app"', unit)
        self.assertIn('WorkingDirectory=', unit)
        with self.assertRaises(ValueError):
            unit_quote('bad\npath')

    def test_book_registration_does_not_copy_or_duplicate(self):
        p = self.root/'book with spaces.zim'
        p.write_bytes(b'ZIM\x04'+b'\x00'*76)
        add_book(p, 'Test book')
        add_book(p, 'Test book')
        registry = json.loads((self.root/'data/books.json').read_text())
        self.assertEqual(len(registry), 1)
        self.assertEqual(registry[0]['path'], str(p.resolve()))
        self.assertEqual(len(list(self.root.rglob('*.zim'))), 1)
        bad = self.root/'bad.zim'
        bad.write_text('not an archive')
        with self.assertRaises(ValueError):
            add_book(bad)

    def test_map_schema_and_bounds(self):
        meta = json.dumps({'vector_layers':[{'id':x} for x in ('roads','water','places')]}).encode()
        header = bytearray(127)
        header[:8] = b'PMTiles\x03'
        struct.pack_into('<QQ', header, 24, 127, len(meta))
        header[97],header[99],header[100],header[101] = 1,1,0,14
        struct.pack_into('<iiii', header, 102, 350500000,330000000,367000000,347500000)
        p = self.root/'map.pmtiles'
        p.write_bytes(bytes(header)+meta)
        self.assertEqual(map_info(p)['maxzoom'], 14)
        self.assertEqual(map_info(p)['bounds'], [35.05,33.0,36.7,34.75])
        header[99] = 2
        p.write_bytes(bytes(header)+meta)
        with self.assertRaises(ValueError):
            map_info(p)

class ServerTests(TemporaryLibrary):
    def setUp(self):
        super().setUp()
        self.data = self.root/'data'
        (self.data/'guides/sample').mkdir(parents=True)
        (self.data/'guides/sample/page.jpg').write_bytes(b'0123456789')
        self.server = Server(('127.0.0.1', 0), Handler)
        self.server.data = self.data
        self.server.kiwix = None
        self.server.kiwix_port = 1
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        super().tearDown()

    def get(self, path, headers=None, method='GET'):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        connection.request(method, path, headers=headers or {})
        r = connection.getresponse()
        result = (r.status, dict(r.getheaders()), r.read())
        connection.close()
        return result

    def test_health_and_empty_library(self):
        status, headers, raw = self.get('/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['app'], 'Switch Field Kit')
        self.assertIn("connect-src 'self'", headers['Content-Security-Policy'])
        data = json.loads(self.get('/api/library')[2])
        self.assertEqual(len(data['guides']), 27)
        self.assertFalse(any(d['installed'] for d in data['guides']))

    def test_ranges_suffixes_invalid_and_head(self):
        path = '/guides/sample/page.jpg'
        status, headers, raw = self.get(path, {'Range':'bytes=2-5'})
        self.assertEqual((status,raw), (206,b'2345'))
        self.assertEqual(headers['Content-Range'], 'bytes 2-5/10')
        self.assertEqual(self.get(path, {'Range':'bytes=-3'})[2], b'789')
        self.assertEqual(self.get(path, {'Range':'bytes=20-'})[0], 416)
        self.assertEqual(self.get(path, {'Range':'bytes=1-2,4-5'})[0], 416)
        self.assertEqual(self.get(path, method='HEAD')[2], b'')

    def test_no_traversal_symlink_or_rebinding(self):
        secret = self.root/'private.txt'
        secret.write_text('must not be served')
        (self.data/'guides/leak.txt').symlink_to(secret)
        for path in ('/guides/%2e%2e/private.txt', '/web/../private.txt', '/guides/leak.txt'):
            self.assertEqual(self.get(path)[0], 403)
        self.assertEqual(self.get('/api/library', {'Host':'attacker.example'})[0], 403)
        self.assertEqual(self.get('/unknown')[0], 404)

if __name__ == '__main__':
    unittest.main()
