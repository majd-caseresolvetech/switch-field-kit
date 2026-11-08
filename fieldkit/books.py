"""Use a separate upstream Kiwix process for user-selected ZIM books."""
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile

from .common import APP, WriterLock, config, data_dir, digest, fetch, read_json, write_json

def install_kiwix():
    arch = {'aarch64':'aarch64', 'arm64':'aarch64', 'x86_64':'x86_64', 'amd64':'x86_64'}.get(platform.machine().lower())
    if platform.system() != 'Linux' or not arch:
        raise RuntimeError('Automatic Kiwix setup supports Linux arm64 and x86_64. Set kiwix_binary in config.json for another system.')
    lock = read_json(APP/'catalogues/tools.json', {})['kiwix'][arch]
    root = data_dir()/'tools'
    archive = fetch(lock['url'], root/lock['filename'], lock['sha256'], lock['bytes'])
    destination = root/'kiwix'
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(str(archive)) as tar:
        for name in ('kiwix-serve', 'kiwix-manage'):
            matches = [m for m in tar.getmembers() if m.isfile() and Path(m.name).name == name]
            if len(matches) != 1:
                raise RuntimeError('Unexpected Kiwix package structure.')
            from .common import atomic
            atomic(destination/name, tar.extractfile(matches[0]).read())
            (destination/name).chmod(0o755)
    subprocess.check_call([str(destination/'kiwix-serve'), '--version'])
    c = config()
    c['kiwix_binary'] = str(destination/'kiwix-serve')
    from .common import config_path
    write_json(config_path(), c)
    print('Kiwix installed. Restart Field Kit after adding a book.')

def add_book(path, title=None):
    path = Path(path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != '.zim':
        raise ValueError('Choose an existing, complete .zim file.')
    with path.open('rb') as f:
        if f.read(4) != b'ZIM\x04':
            raise ValueError('This does not have a ZIM archive header.')
    with WriterLock():
        registry = data_dir()/'books.json'
        books = read_json(registry, [])
        if any(b['path'] == str(path) for b in books):
            print('This book is already registered.')
            return
        import hashlib
        ident = hashlib.sha256(str(path).encode()).hexdigest()[:16]
        books.append({'id':ident, 'title':title or path.stem.replace('_', ' '), 'path':str(path), 'bytes':path.stat().st_size})
        write_json(registry, books)
    print('Added without copying: '+str(path))
    print('Leave this file in place. Run: fieldkit restart')

def start_kiwix(settings, port):
    books = read_json(Path(settings['data'])/'books.json', [])
    paths = [b['path'] for b in books if Path(b['path']).is_file()]
    if not paths:
        return None
    binary = settings.get('kiwix_binary') or shutil.which('kiwix-serve')
    if not binary:
        print('Books need Kiwix. Run: fieldkit kiwix', flush=True)
        return None
    args = [binary, '--address=127.0.0.1', '--port='+str(port), '--urlRootLocation=/kiwix', '--threads=2'] + paths
    log = (Path(settings['data'])/'kiwix.log').open('a')
    try:
        return subprocess.Popen(args, stdout=log, stderr=log)
    except OSError as e:
        print('Kiwix could not start: '+str(e)+'. Guides and maps are still available. Repair with ~/.local/bin/fieldkit kiwix, then restart.', flush=True)
        return None
    finally:
        log.close()
