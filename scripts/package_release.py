from pathlib import Path
import hashlib
import json
import sys
import zipfile
from audit_release import ROOT, audit, files

audit()
out=ROOT/'dist';out.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))
from fieldkit import __version__
version=__version__;name='switch-field-kit-'+version;target=out/(name+'.zip')
with zipfile.ZipFile(str(target),'w',zipfile.ZIP_DEFLATED) as archive:
    for path in files():
        info=zipfile.ZipInfo(name+'/'+str(path.relative_to(ROOT)),date_time=(2026,11,8,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o100755 if path.name=='setup.sh' else 0o100644)<<16
        archive.writestr(info,path.read_bytes())
sha=hashlib.sha256(target.read_bytes()).hexdigest()
(out/'SHA256SUMS').write_text(sha+'  '+target.name+'\n')
print(json.dumps({'file':str(target),'bytes':target.stat().st_size,'sha256':sha},indent=2))
