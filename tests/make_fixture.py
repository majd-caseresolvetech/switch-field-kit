"""Generate original test pages. Never download publisher content in CI."""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from fieldkit.common import catalogue, data_dir
from fieldkit.content import install_one

def pdf_bytes(count=9):
    objects={1:b'<< /Type /Catalog /Pages 2 0 R >>',3:b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'}
    kids=[]
    for n in range(count):
        page=4+n*2;stream=page+1;kids.append(str(page)+' 0 R')
        content=('BT /F1 20 Tf 45 740 Td (Field Kit test page %d) Tj 0 -34 Td /F1 12 Tf (Shelter category navigation fixture. No survival instructions.) Tj ET 45 350 350 270 re S 55 360 80 80 re S' % (n+1)).encode()
        objects[page]=('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 500 800] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>' % stream).encode()
        objects[stream]=b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream'
    objects[2]=('<< /Type /Pages /Count %d /Kids [%s] >>' % (count,' '.join(kids))).encode()
    raw=b'%PDF-1.4\n';offsets=[0]
    for ident in range(1,max(objects)+1):
        offsets.append(len(raw));raw+=str(ident).encode()+b' 0 obj\n'+objects[ident]+b'\nendobj\n'
    start=len(raw);raw+=('xref\n0 %d\n0000000000 65535 f \n' % len(offsets)).encode()
    raw+=b''.join(('%010d 00000 n \n' % offset).encode() for offset in offsets[1:])
    raw+=('trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(offsets),start)).encode()
    return raw

if __name__=='__main__':
    d=dict(catalogue()[0]);raw=pdf_bytes(d['pages'])
    d.update(title='Navigation test document',original='Original test fixture',author='Field Kit test suite',publisher='Test fixture',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    p=data_dir()/'guides'/d['id']/'original.pdf';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    install_one(d)
