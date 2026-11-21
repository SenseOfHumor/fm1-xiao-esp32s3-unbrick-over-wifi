"""Targeted approval guards. No hardware connections or write simulation."""
from pathlib import Path
from types import SimpleNamespace
import pytest
import esp32_recover as bridge
from approved_v15 import ApprovedTransport,check_plan,ORIGINAL,FINAL,IDENTITY,sha

@pytest.fixture
def approved():
    f=bridge.ftr
    root=Path(__file__).resolve().parents[1]
    ref_path=root/'logs/attempt-20261121-021358/flash-backups/full-flash-before-1.bin'
    if not ref_path.exists() or not (root/'third_party/FM1Backups/V15-FM-1.fwsc').exists():
        pytest.skip('private real-device fixture and V15 are not distributed')
    ref=ref_path.read_bytes()
    pkg=f.load_restore_package(root/'third_party/FM1Backups/V15-FM-1.fwsc',True)
    plan=f.Plan(pkg,ref,Path('saved real backup'))
    return f,plan,check_plan(f,plan)

def test_actual_approved_plan(approved):
    f,p,expected=approved
    assert sha(p.ref)==ORIGINAL and sha(expected)==FINAL and len(p.write)==143
    assert expected[:0x4000]==p.ref[:0x4000] and expected[0x93000:]==p.ref[0x93000:]

def test_changed_protected_data_stops_before_writes(approved,tmp_path):
    f,p,e=approved
    changed=bytearray(p.ref);changed[0xe7f00]^=1
    t=SimpleNamespace(read_flash=lambda *a:bytes(changed))
    guard=ApprovedTransport(t,f,p,e,tmp_path)
    with pytest.raises(f.fu.SafetyError,match='including protected data'):guard.read_flash(0,0x100000)
    assert not guard.fresh_verified and not (tmp_path/'write-journal.jsonl').exists()

@pytest.mark.parametrize('addr',[0,0x3000,0x93000,0xe6000,0xe7f00])
def test_protected_or_unapproved_sector_refused(approved,tmp_path,addr):
    f,p,e=approved
    guard=ApprovedTransport(SimpleNamespace(),f,p,e,tmp_path);guard.fresh_verified=True
    with pytest.raises(f.fu.SafetyError):guard.write_sector(addr,b'\xff'*4096)
    assert not (tmp_path/'write-journal.jsonl').exists()

def test_wrong_identity_refused(approved,tmp_path):
    f,p,e=approved
    guard=ApprovedTransport(SimpleNamespace(info=lambda:'OK key=980F type=3 id=B36014'),f,p,e,tmp_path)
    with pytest.raises(f.fu.SafetyError,match='identity'):guard.info()

def test_wrong_payload_refused(approved,tmp_path):
    f,p,e=approved
    guard=ApprovedTransport(SimpleNamespace(),f,p,e,tmp_path);guard.fresh_verified=True
    wrong=bytearray(e[0x4000:0x5000]);wrong[0]^=1
    with pytest.raises(f.fu.SafetyError):guard.write_sector(0x4000,wrong)
    assert not (tmp_path/'write-journal.jsonl').exists()
