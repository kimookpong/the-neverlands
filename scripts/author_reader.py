"""Copy the read-only author viewer and an opaque encrypted snapshot only."""
import base64
import json
from pathlib import Path
import shutil

FILES={'index.html','styles.css','reader.js','crypto.mjs','vault.json'}


def validate_envelope(path):
    envelope=json.loads(Path(path).read_text(encoding='utf-8'))
    assert set(envelope)=={'version','kdf','iterations','cipher','salt','iv','ciphertext'}, 'Unexpected author envelope fields'
    assert envelope['version']==1 and envelope['kdf']=='PBKDF2-SHA256' and envelope['iterations']==600000
    assert envelope['cipher']=='AES-256-GCM'
    assert len(base64.b64decode(envelope['salt'],validate=True))==16
    assert len(base64.b64decode(envelope['iv'],validate=True))==12
    assert 16<len(base64.b64decode(envelope['ciphertext'],validate=True))<20*1024*1024


def export_writer(root,out,base):
    source=root/'site/writer'
    assert {p.name for p in source.iterdir() if p.is_file()}==FILES, 'Author viewer has missing or unexpected files'
    validate_envelope(source/'vault.json')
    target=out/'writer';target.mkdir()
    for name in FILES:
        if name=='index.html':
            (target/name).write_text((source/name).read_text(encoding='utf-8').replace('__BASE__',base),encoding='utf-8')
        else:
            shutil.copyfile(source/name,target/name)


def validate_export(out):
    target=out/'writer'
    assert {p.name for p in target.iterdir()}==FILES
    validate_envelope(target/'vault.json')
    source=(target/'reader.js').read_text(encoding='utf-8')
    forbidden=('localStorage','sessionStorage','indexedDB','sendBeacon','XMLHttpRequest','/api/','serviceWorker','innerHTML','outerHTML','contentEditable')
    assert not any(term in source for term in forbidden), 'Read-only viewer must not persist data or inject markup'
    assert source.count('fetch(')==1 and "new URL('vault.json',location.href)" in source
    assert "cache:'no-store',credentials:'omit'" in source
    page=(target/'index.html').read_text(encoding='utf-8')
    assert 'noindex, nofollow, noarchive' in page
    assert '<textarea' not in page and 'type="file"' not in page
