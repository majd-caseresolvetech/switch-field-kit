"""Optional Protomaps downloads and local map registration."""
import datetime
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import tarfile
import time
import urllib.request
import zipfile

from .common import APP, WriterLock, atomic, data_dir, digest, enough_space, fetch, read_json, write_json

PRESETS = {
    'world': {'name':'World overview', 'zoom':6, 'bbox':None},
    'uk': {'name':'UK roads and places', 'zoom':13, 'bbox':[-8.8,49.7,2,61]},
    'lebanon': {'name':'Lebanon roads and places', 'zoom':14, 'bbox':[35.05,33,36.7,34.75]},
    'prague': {'name':'Prague streets and paths', 'zoom':15, 'bbox':[14.15,49.9,14.8,50.25]},
    'europe-levant': {'name':'Europe to Levant overview', 'zoom':10, 'bbox':[-6,32,45,56.2]},
}

def install_map_tools():
    locks = read_json(APP/'catalogues/tools.json')
    root = data_dir()
    assets = root/'map-assets'
    assets.mkdir(parents=True, exist_ok=True)
    with WriterLock():
        for item in locks['map_packages']:
            archive = fetch(item['url'], root/'tools'/item['filename'], item['sha256'], item['bytes'])
            with tarfile.open(str(archive)) as tar:
                for member in tar.getmembers():
                    name = member.name
                    allowed = name.startswith('package/dist/') and name.endswith(('.js', '.mjs', '.css'))
                    licence = Path(name).name.lower().startswith(('license', 'licence'))
                    if member.isfile() and (allowed or licence):
                        destination = assets/Path(name).name if allowed else assets/'licenses'/(item['name']+'-'+Path(name).name)
                        atomic(destination, tar.extractfile(member).read())
        item = locks['map_assets']
        archive = fetch(item['url'], root/'tools'/item['filename'], item['sha256'], item['bytes'])
        with zipfile.ZipFile(str(archive)) as z:
            for info in z.infolist():
                parts = Path(info.filename).parts[1:]
                if not parts or '..' in parts or info.is_dir():
                    continue
                rel = Path(*parts)
                name = str(rel)
                if name.startswith('fonts/') and name.endswith('.pbf'):
                    atomic(assets/rel, z.read(info))
                elif name.startswith('sprites/v4/') and name.endswith(('.png', '.json')):
                    atomic(assets/'sprites'/rel.name, z.read(info))
                elif any(s in rel.name.lower() for s in ('license', 'licence', 'ofl')):
                    atomic(assets/'licenses'/'basemap-assets'/rel, z.read(info))
        write_json(assets/'sources.json', {k:locks[k] for k in ('map_packages', 'map_assets')})
    print('Offline map viewer, fonts and symbols are ready.')

def map_info(path):
    path = Path(path)
    with path.open('rb') as f:
        header = f.read(127)
        if len(header) != 127 or header[:8] != b'PMTiles\x03' or header[99] != 1:
            raise ValueError('Use a PMTiles v3 vector archive with Protomaps v4 layers.')
        offset, length = struct.unpack_from('<QQ', header, 24)
        if length > 2*1024*1024 or offset+length > path.stat().st_size:
            raise ValueError('Invalid map metadata size.')
        f.seek(offset)
        raw = f.read(length)
    if header[97] == 2:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as z:
            raw = z.read(10*1024*1024+1)
    elif header[97] != 1:
        raise ValueError('Unsupported metadata compression. Use a standard Protomaps download.')
    if len(raw) > 10*1024*1024:
        raise ValueError('Map metadata is too large.')
    meta = json.loads(raw.decode('utf-8'))
    layers = {v.get('id') for v in meta.get('vector_layers', [])}
    if not {'roads','water','places'}.issubset(layers):
        raise ValueError('This archive uses another map schema. The reader currently supports Protomaps v4.')
    bounds = [v/1e7 for v in struct.unpack_from('<iiii', header, 102)]
    if not (-180 <= bounds[0] < bounds[2] <= 180 and -90 <= bounds[1] < bounds[3] <= 90):
        raise ValueError('Invalid map bounds.')
    return {'bounds':bounds, 'minzoom':header[100], 'maxzoom':header[101],
            'edition':meta.get('planetiler:osm:osmosisreplicationtime', 'Date not recorded'),
            'bytes':path.stat().st_size}

def add_map(path, name):
    path = Path(path).expanduser().resolve()
    info = map_info(path)
    ident = hashlib.sha256(str(path).encode()).hexdigest()[:16]
    info.update(id=ident, name=name, path=str(path))
    with WriterLock():
        registry = data_dir()/'maps.json'
        maps = [m for m in read_json(registry, []) if m['id'] != ident]
        maps.append(info)
        write_json(registry, maps)
    print('Map registered without copying: '+name)
    return info

def pmtiles_tool():
    arch = {'aarch64':'aarch64','arm64':'aarch64','x86_64':'x86_64'}.get(platform.machine().lower())
    if platform.system() != 'Linux' or not arch:
        found = shutil.which('pmtiles')
        if found:
            return found
        raise RuntimeError('Install the upstream pmtiles CLI for this system. Automatic setup supports Linux arm64 and x86_64.')
    item = read_json(APP/'catalogues/tools.json')['pmtiles'][arch]
    root = data_dir()/'tools'
    archive = fetch(item['url'], root/item['filename'], item['sha256'], item['bytes'])
    target = root/'pmtiles'
    with tarfile.open(str(archive)) as tar:
        match = [m for m in tar.getmembers() if m.isfile() and Path(m.name).name == 'pmtiles']
        if len(match) != 1:
            raise RuntimeError('Unexpected pmtiles package layout.')
        atomic(target, tar.extractfile(match[0]).read())
        target.chmod(0o755)
    return str(target)

def source_url(date=None):
    if date:
        datetime.datetime.strptime(date, '%Y%m%d')
        return 'https://build.protomaps.com/'+date+'.pmtiles'
    today = datetime.datetime.utcnow().date()
    for ago in range(8):
        date = (today-datetime.timedelta(days=ago)).strftime('%Y%m%d')
        url = 'https://build.protomaps.com/'+date+'.pmtiles'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'Range':'bytes=0-126'}), timeout=10) as r:
                if r.status == 206 and r.read(8) == b'PMTiles\x03':
                    return url
        except OSError:
            continue
    raise RuntimeError('Could not find a recent map build. Check https://maps.protomaps.com/builds and pass --date YYYYMMDD.')

def download_map(preset, date=None, yes=False, plan=False):
    if preset not in PRESETS:
        raise ValueError('Choose: '+', '.join(PRESETS))
    tool = pmtiles_tool()
    source = source_url(date)
    region = PRESETS[preset]
    root = data_dir()/'maps'
    root.mkdir(parents=True, exist_ok=True)
    target = root/(preset+'.pmtiles')
    temp = root/(preset+'.incoming.pmtiles')
    flags = ['--maxzoom='+str(region['zoom']), '--download-threads=2']
    if region['bbox']:
        flags += ['--bbox='+','.join(str(x) for x in region['bbox'])]
    print('Calculating download size for '+region['name']+' from '+source, flush=True)
    result = subprocess.check_output([tool, 'extract', source, str(temp), '--dry-run']+flags, stderr=subprocess.STDOUT, universal_newlines=True)
    print(result)
    match = re.search(r'archive size of\s+([\d.]+)\s*(B|kB|KB|MB|GB|TB)\b', result)
    if not match:
        raise RuntimeError('Could not read the download size. No map was downloaded.')
    multiplier = {'B':1,'kB':1000,'KB':1000,'MB':1000000,'GB':1000000000,'TB':1000000000000}[match[2]]
    required = int(float(match[1])*multiplier*1.2)+32*1024*1024
    enough_space(root, required)
    if plan:
        return
    from .install import ask
    if not yes and not ask('Download this map now?'):
        print('No map downloaded.')
        return
    with WriterLock():
        if temp.exists():
            temp.unlink()
        process = subprocess.Popen([tool, 'extract', source, str(temp)]+flags)
        try:
            while process.poll() is None:
                if shutil.disk_usage(str(root)).free < 512*1024*1024:
                    process.terminate()
                    raise RuntimeError('Stopped to preserve 512 MB of free space. Use a smaller preset or a larger storage folder.')
                time.sleep(1)
            if process.returncode:
                raise RuntimeError('Map extraction failed. Retry the command. The previous map is unchanged.')
            subprocess.check_call([tool, 'verify', str(temp)])
            map_info(temp)
            os.replace(str(temp), str(target))
            write_json(root/(preset+'.source.json'), {'source':source,'preset':region,'sha256':digest(target),'licence':'OpenStreetMap ODbL 1.0 / Protomaps data attribution'})
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    add_map(target, region['name'])
    print('Map saved. Refresh the Maps tab. Run fieldkit map-tools if its viewer assets are not installed.')
