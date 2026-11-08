"""Preserve original PDFs and render their complete pages locally."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from .common import APP, WriterLock, catalogue, data_dir, digest, enough_space, fetch, read_json, write_json

def pdf_tools():
    missing = [p for p in ('pdfinfo', 'pdftoppm', 'pdftotext') if not shutil.which(p)]
    if missing:
        raise RuntimeError('PDF tools are missing: '+', '.join(missing)+'. Run: sudo apt install poppler-utils')

def install_guides(selection):
    docs = catalogue()
    if selection != 'all':
        wanted = set(selection.split(','))
        unknown = wanted - {d['id'] for d in docs}
        if unknown:
            raise ValueError('Unknown guide: '+', '.join(sorted(unknown)))
        docs = [d for d in docs if d['id'] in wanted]
    pdf_tools()
    failures = []
    with WriterLock():
        for d in docs:
            try:
                install_one(d)
            except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
                failures.append(d['id'])
                print('Could not install %s: %s' % (d['id'], e), flush=True)
    if failures:
        raise RuntimeError('These guides remain unavailable: '+', '.join(failures)+'. Installed guides are ready. Retry with: fieldkit guides '+','.join(failures))

def install_one(d):
    root = data_dir()/'guides'/d['id']
    root.mkdir(parents=True, exist_ok=True)
    previous = read_json(root/'publication.json', {})
    complete = previous.get('source_sha256') == d['sha256'] and previous.get('pages') == d['pages']
    complete = complete and (root/'original.pdf').is_file() and digest(root/'original.pdf') == d['sha256']
    complete = complete and all((root/('%03d.jpg' % n)).is_file() for n in range(1, d['pages']+1))
    if complete:
        print('Ready: '+d['title'], flush=True)
        return
    enough_space(root, d['bytes'] + d['pages']*1600000)
    print('Downloading original: '+d['title'], flush=True)
    pdf = fetch(d['url'], root/'original.pdf', d['sha256'], d['bytes'])
    env = dict(os.environ, LC_ALL='C')
    info = subprocess.check_output(['pdfinfo', str(pdf)], env=env, universal_newlines=True)
    match = re.search(r'^Pages:\s+(\d+)', info, re.M)
    if not match or int(match.group(1)) != d['pages']:
        raise RuntimeError('The PDF page count differs from the checked edition.')
    text = subprocess.check_output(['pdftotext', '-layout', '-enc', 'UTF-8', str(pdf), '-']).decode('utf-8', errors='replace').split('\f')
    if len(text) > d['pages']:
        text = text[:d['pages']]
    text += ['']*(d['pages']-len(text))
    for page in range(1, d['pages']+1):
        image = root/('%03d.jpg' % page)
        if not image.exists() or previous.get('source_sha256') != d['sha256']:
            temp = root/('.render-%03d' % page)
            subprocess.check_call(['pdftoppm', '-f', str(page), '-singlefile', '-scale-to', '2400',
                                   '-jpeg', '-jpegopt', 'quality=90', str(pdf), str(temp)], stdout=subprocess.DEVNULL)
            made = Path(str(temp)+'.jpg')
            if not made.exists() or not made.read_bytes().startswith(b'\xff\xd8'):
                raise RuntimeError('A PDF page could not render.')
            os.replace(str(made), str(image))
        print('  Saved page %d / %d' % (page, d['pages']), flush=True)
    saved = dict(d)
    saved.update(source_sha256=d['sha256'], saved_at=time.strftime('%Y-%m-%d'),
                 text=['']*d['pages'] if d.get('section_search_only') else text)
    write_json(root/'publication.json', saved)
    print('Ready offline: '+d['title'], flush=True)

def verify_content():
    issues = []
    ready = 0
    root = data_dir()
    for d in catalogue():
        directory = root/'guides'/d['id']
        if not (directory/'publication.json').exists():
            continue
        if not (directory/'original.pdf').exists() or digest(directory/'original.pdf') != d['sha256']:
            issues.append(d['id']+': PDF checksum mismatch')
        for n in range(1, d['pages']+1):
            p = directory/('%03d.jpg' % n)
            if not p.is_file() or p.stat().st_size < 100:
                issues.append(d['id']+': missing page '+str(n))
        ready += 1
    return {'ready_guides': ready, 'available_guides': len(catalogue()), 'issues': issues}
