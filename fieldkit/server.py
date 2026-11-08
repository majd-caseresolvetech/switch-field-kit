"""Read-only loopback HTTP server. No public network listener or write API."""
import http.client
import http.server
import json
import mimetypes
import os
from pathlib import Path
import re
import signal
import socketserver
from urllib.parse import unquote, urlsplit

from .common import APP, catalogue, config, data_dir, read_json
from .books import start_kiwix
from . import __version__

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; worker-src 'self' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'")
        super().end_headers()

    def send_bytes(self, raw, kind, status=200):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(raw)

    def json(self, value, status=200):
        self.send_bytes(json.dumps(value, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8', status)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        try:
            self.handle_get()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def handle_get(self):
        host = self.headers.get('Host', '').split(':')[0]
        if host not in ('127.0.0.1', 'localhost'):
            self.send_error(403, 'Use the localhost address shown by Field Kit.')
            return
        path = unquote(urlsplit(self.path).path)
        if '\x00' in path or '\\' in path or '..' in path.split('/'):
            self.send_error(403)
            return
        root = self.server.data
        if path == '/api/library':
            docs = []
            for d in catalogue():
                item = dict(d)
                item['installed'] = (root/'guides'/d['id']/'publication.json').is_file()
                docs.append(item)
            books = read_json(root/'books.json', [])
            maps = read_json(root/'maps.json', [])
            self.json({'guides':docs, 'books':[{'title':b['title'], 'available':Path(b['path']).is_file()} for b in books],
                       'maps':maps, 'version':__version__, 'kiwix_running':bool(self.server.kiwix and self.server.kiwix.poll() is None),
                       'map_tools_ready':(root/'map-assets/sources.json').is_file()})
            return
        if path == '/api/health':
            self.json({'app':'Switch Field Kit', 'version':__version__, 'offline':True})
            return
        if path.startswith('/kiwix/'):
            self.proxy_kiwix()
            return
        if path in ('/', '/index.html'):
            self.file(APP/'web/index.html')
            return
        if path.startswith('/web/'):
            self.safe_file(APP/'web', path[5:])
            return
        if path.startswith('/guides/'):
            self.safe_file(root/'guides', path[8:])
            return
        if path.startswith('/map-assets/'):
            self.safe_file(root/'map-assets', path[12:])
            return
        match = re.fullmatch(r'/map-data/([a-z0-9-]+)\.pmtiles', path)
        if match:
            item = next((m for m in read_json(root/'maps.json', []) if m['id'] == match.group(1)), None)
            if item:
                self.file(Path(item['path']))
                return
        self.send_error(404)

    def safe_file(self, base, relative):
        base = base.resolve()
        dest = (base/relative).resolve()
        if base not in dest.parents:
            self.send_error(403)
        else:
            self.file(dest)

    def file(self, path):
        if not path.is_file():
            self.send_error(404)
            return
        size = path.stat().st_size
        start, end, status = 0, size-1, 200
        header = self.headers.get('Range')
        if header:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', header)
            try:
                if not match or not any(match.groups()):
                    raise ValueError()
                if not match[1]:
                    start = max(0, size-int(match[2]))
                else:
                    start = int(match[1])
                    if match[2]:
                        end = min(end, int(match[2]))
                if start > end or start >= size:
                    raise ValueError()
            except ValueError:
                self.send_response(416)
                self.send_header('Content-Range', 'bytes */'+str(size))
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            status = 206
        self.send_response(status)
        mime = 'text/javascript' if path.suffix in ('.js', '.mjs') else mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.send_header('Content-Type', mime)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(max(0, end-start+1)))
        if status == 206:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Cache-Control', 'no-cache' if path.suffix in ('.html', '.js', '.json', '.css') else 'private, max-age=86400')
        self.end_headers()
        if self.command != 'HEAD':
            with path.open('rb') as f:
                f.seek(start)
                left = end-start+1
                while left > 0:
                    block = f.read(min(left, 65536))
                    if not block:
                        break
                    self.wfile.write(block)
                    left -= len(block)

    def proxy_kiwix(self):
        if not self.server.kiwix or self.server.kiwix.poll() is not None:
            self.send_bytes(b'Kiwix is not running. Use fieldkit kiwix, add a .zim book, then fieldkit restart.', 'text/plain', 503)
            return
        connection = http.client.HTTPConnection('127.0.0.1', self.server.kiwix_port, timeout=30)
        try:
            headers = {'Accept-Encoding':'identity'}
            if self.headers.get('Range'):
                headers['Range'] = self.headers['Range']
            connection.request(self.command, self.path, headers=headers)
            response = connection.getresponse()
            content_type = response.getheader('Content-Type', '')
            html = self.command != 'HEAD' and 'text/html' in content_type
            raw = response.read() if html else None
            if html:
                addition = b'<link rel="stylesheet" href="/web/book-theme.css"><script src="/web/book-theme.js" defer></script>'
                raw = raw.replace(b'</head>', addition+b'</head>', 1)
                if urlsplit(self.path).path == '/kiwix/viewer':
                    raw = raw.replace(b'onload="on_content_load()"', b'onload="if (typeof on_content_load === \'function\') on_content_load()"')
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in ('connection', 'transfer-encoding', 'content-length', 'content-security-policy', 'x-content-type-options', 'referrer-policy', 'content-encoding'):
                    self.send_header(key, value)
            length = len(raw) if html else response.getheader('Content-Length')
            if length is not None:
                self.send_header('Content-Length', str(length))
            else:
                self.send_header('Connection', 'close')
                self.close_connection = True
            self.end_headers()
            if self.command != 'HEAD':
                if html:
                    self.wfile.write(raw)
                else:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
        except (OSError, http.client.HTTPException):
            self.close_connection = True
        finally:
            connection.close()

def serve(port=None, kiwix_port=None):
    settings = config()
    port = port or settings['port']
    kp = kiwix_port or settings['kiwix_port']
    server = Server(('127.0.0.1', port), Handler)
    server.data = data_dir()
    server.kiwix_port = kp
    server.kiwix = start_kiwix(settings, kp)
    def stop(*args):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    print('Switch Field Kit: http://127.0.0.1:%d' % port, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if server.kiwix and server.kiwix.poll() is None:
            server.kiwix.terminate()
            try:
                server.kiwix.wait(timeout=10)
            except __import__('subprocess').TimeoutExpired:
                server.kiwix.kill()
                server.kiwix.wait()
