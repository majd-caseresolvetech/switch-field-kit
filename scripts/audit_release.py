"""Fail if private data, publisher files or generated downloads enter a release."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
ALLOW_DIRS = {'fieldkit','web','catalogues','docs','tests','scripts','.github'}
ALLOW_FILES = {'README.md','LICENSE','THIRD_PARTY.md','CONTRIBUTING.md','SECURITY.md','RELEASE_NOTES.md',
               '.gitignore','setup.sh','package.json','package-lock.json'}

def files():
    result = []
    for name in sorted(ALLOW_DIRS):
        for p in sorted((ROOT/name).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                result.append(p)
    result += [ROOT/name for name in sorted(ALLOW_FILES) if (ROOT/name).is_file()]
    return sorted(result)

def audit():
    problems=[]
    patterns=[re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
              re.compile(rb'gh[pousr]_[A-Za-z0-9]{25,}'),
              re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),
              re.compile(rb'192\.168\.\d+\.\d+'),
              re.compile(('/'+'Users'+r'/[A-Za-z0-9_.-]+/').encode())]
    for p in files():
        relative=p.relative_to(ROOT)
        if p.is_symlink():problems.append(str(relative)+': symlinks are not release content')
        if p.suffix.lower() in {'.pdf','.zim','.pmtiles','.pem','.key','.pbf','.tgz','.tar','.zip','.gz','.sqlite'}:
            problems.append(str(relative)+': downloaded/private file type')
        if p.stat().st_size>2*1024*1024:problems.append(str(relative)+': unexpectedly large source file')
        raw=p.read_bytes()
        if p.suffix.lower() not in {'.png','.jpg'}:
            for pattern in patterns:
                if pattern.search(raw):problems.append(str(relative)+': private-data pattern')
        if raw.startswith(b'%PDF-'):problems.append(str(relative)+': embedded publisher PDF')
    docs=json.loads((ROOT/'catalogues/guides.json').read_text())
    if len(docs)!=27 or any('text' in d for d in docs):problems.append('Unexpected guide catalogue or publisher full text')
    if problems:
        raise RuntimeError('\n'.join(problems))
    print('Release audit passed: %d allowlisted files. No downloaded books or private credentials.' % len(files()))

if __name__=='__main__':
    try:audit()
    except RuntimeError as e:
        print(e,file=sys.stderr);sys.exit(1)
