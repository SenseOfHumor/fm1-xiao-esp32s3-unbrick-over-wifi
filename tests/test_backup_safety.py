import json
import pytest
from backup_safety import preserve_pair,validate_pair,validate_reference

@pytest.fixture
def image(): return bytes(i%251 for i in range(1024*1024))

def test_independent_backup_preservation(tmp_path,image):
    sha=preserve_pair(tmp_path,[image,bytes(bytearray(image))])
    (tmp_path/'analysis.json').write_text(json.dumps({'sha256':sha}))
    assert validate_reference(tmp_path/'full-flash-before-1.bin')==sha
    with pytest.raises(FileExistsError):preserve_pair(tmp_path,[image,image])

def test_mismatching_reads(image):
    with pytest.raises(ValueError,match='differ'):validate_pair(image,image[:-1]+b'x')

def test_short_reads():
    with pytest.raises(ValueError,match='1 MiB'):validate_pair(b'one',b'one')

def test_reference_manifest_tampering(tmp_path,image):
    preserve_pair(tmp_path,[image,image])
    (tmp_path/'analysis.json').write_text(json.dumps({'sha256':'wrong'}))
    with pytest.raises(ValueError,match='manifest'):validate_reference(tmp_path/'full-flash-before-1.bin')

def test_write_authorization_blocks_before_connection(monkeypatch,tmp_path):
    import wifi_recover
    path=tmp_path/'credentials.json'
    path.write_text(json.dumps(dict(host='127.0.0.1',port=3333,secret='secret')))
    monkeypatch.setattr(wifi_recover,'TcpTransport',lambda *a,**k:pytest.fail('must not connect'))
    with pytest.raises(SystemExit):wifi_recover.main(['--credentials',str(path),'restore','stock.fwsc','--write'])

def test_mock_backups_cannot_plan_real_restore(tmp_path,image):
    sha=preserve_pair(tmp_path,[image,image])
    (tmp_path/'analysis.json').write_text(json.dumps({'sha256':sha,'mock':True}))
    with pytest.raises(ValueError,match='simulated'):validate_reference(tmp_path/'full-flash-before-1.bin')
    assert validate_reference(tmp_path/'full-flash-before-1.bin',allow_mock=True)==sha
