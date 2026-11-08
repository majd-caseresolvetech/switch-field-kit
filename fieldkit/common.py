"""Paths, verified downloads and atomic state. Python 3.6+ stdlib only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
from urllib.parse import urlparse

APP = Path(__file__).resolve().parent.parent

def config_path():
    base = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))
    return Path(os.environ.get('FIELDKIT_CONFIG', str(base/'switch-field-kit/config.json'))).expanduser()

def config():
    p = config_path()
    value = json.loads(p.read_text()) if p.exists() else {}
    value.setdefault('data', str(Path.home()/'SwitchFieldKit'))
    value.setdefault('port', 8095)
    value.setdefault('kiwix_port', 8096)
    if os.environ.get('FIELDKIT_DATA'):
        value['data'] = os.environ['FIELDKIT_DATA']
    value['data'] = str(Path(value['data']).expanduser().resolve())
    for key in ('port', 'kiwix_port'):
        if not isinstance(value[key], int) or not 1024 <= value[key] <= 65535:
            raise ValueError('Choose an unused port from 1024 to 65535.')
    if value['port'] == value['kiwix_port']:
        raise ValueError('The library and Kiwix ports must be different.')
    return value

def data_dir():
    p = Path(config()['data'])
    p.mkdir(parents=True, exist_ok=True)
    return p

def atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=str(path.parent), prefix='.'+path.name)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, str(path))
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def write_json(path, value):
    atomic(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def read_json(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def enough_space(path, required):
    free = shutil.disk_usage(str(path)).free
    reserve = 512*1024*1024
    if free < required + reserve:
        raise RuntimeError('Not enough space. Need about %.1f MB plus 512 MB left free. Choose a larger Linux storage folder.' % (required/1e6))

def fetch(url, destination, sha256, size):
    """Download to a partial file, require HTTPS and an expected SHA-256."""
    if urlparse(url).scheme != 'https' or len(sha256) != 64 or size <= 0:
        raise ValueError('A pinned HTTPS URL, size and SHA-256 are required.')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == size and digest(destination) == sha256:
        return destination
    enough_space(destination.parent, size)
    partial = destination.with_name(destination.name+'.part')
    if partial.exists() and partial.stat().st_size >= size:
        partial.unlink()
    args = ['curl', '--fail', '--location', '--proto', '=https', '--proto-redir', '=https',
            '--connect-timeout', '20', '--max-time', '1800', '--retry', '2',
            '--max-filesize', str(size), '--output', str(partial)]
    if partial.exists():
        args += ['--continue-at', '-']
    try:
        if shutil.which('curl'):
            subprocess.check_call(args+[url])
        else:
            class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, request, response, code, message, headers, newurl):
                    if urlparse(newurl).scheme != 'https':
                        raise RuntimeError('Refused a download redirect away from HTTPS.')
                    return super().redirect_request(request, response, code, message, headers, newurl)
            offset = partial.stat().st_size if partial.exists() else 0
            headers = {'User-Agent':'SwitchFieldKit/0.1 (+https://github.com/majd-caseresolvetech/switch-field-kit)'}
            if offset:
                headers['Range'] = 'bytes='+str(offset)+'-'
            with urllib.request.build_opener(HTTPSRedirect()).open(urllib.request.Request(url, headers=headers), timeout=60) as response:
                resume = offset and response.status == 206
                if resume and not response.headers.get('Content-Range', '').startswith('bytes '+str(offset)+'-'):
                    raise RuntimeError('Publisher returned the wrong resume range.')
                received = offset if resume else 0
                with partial.open('ab' if resume else 'wb') as f:
                    while True:
                        chunk = response.read(1024*1024)
                        if not chunk:
                            break
                        received += len(chunk)
                        if received > size:
                            raise RuntimeError('Publisher download exceeded the checked size.')
                        f.write(chunk)
    except (subprocess.CalledProcessError, OSError):
        raise RuntimeError('Download interrupted. Run the same command to retry. If this publisher rejects resume, remove only '+str(partial)+' and retry.')
    if partial.stat().st_size != size or digest(partial) != sha256:
        partial.unlink()
        raise RuntimeError('The download does not match the verified edition. Nothing was installed. Check for a newer Field Kit release.')
    os.replace(str(partial), str(destination))
    return destination

def catalogue():
    return read_json(APP/'catalogues/guides.json', [])

class WriterLock:
    def __enter__(self):
        import fcntl
        self.file = (data_dir()/'.write-lock').open('a')
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError('Another Field Kit download or import is running. Let it finish first.')
        return self

    def __exit__(self, *args):
        self.file.close()
