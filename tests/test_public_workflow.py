"""Portable approval and credential guards; no private device fixture required."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import esp32_recover as bridge
from approved_v15 import Approval, PACKAGE, check_plan, sha, read_approval
from configure_wifi import generate


def test_credentials_do_not_rotate_implicitly(tmp_path):
    first=generate(tmp_path)
    with pytest.raises(FileExistsError):generate(tmp_path)
    assert json.loads((tmp_path/'wifi_credentials.json').read_text())==first
    second=generate(tmp_path,True)
    assert second!=first and len(list(tmp_path.glob('*.backup')))==2


def synthetic():
    old=b'\x00'*0x4000+b'A'*0x1000+b'\xff'*(0x100000-0x5000)
    new=old[:0x4000]+b'B'*0x1000+old[0x5000:0x93000]
    pkg=SimpleNamespace(flash=new,file_sha256=PACKAGE,kind='official-v15')
    plan=bridge.ftr.Plan(pkg,old,Path('synthetic-unit-test'))
    expected=old[:0x4000]+new[0x4000:]+old[0x93000:]
    approval=Approval(sha(old),sha(expected),'OK key=980F type=3 id=856014',(0x4000,),Path('not-a-real-backup'))
    return plan,approval,expected


def test_generic_approval_is_not_bound_to_case_hashes():
    plan,approval,expected=synthetic()
    assert check_plan(bridge.ftr,plan,approval)==expected
    assert expected[:0x4000]==plan.ref[:0x4000] and expected[0x93000:]==plan.ref[0x93000:]


def test_generic_approval_cannot_widen_sector_range():
    plan,approval,expected=synthetic()
    bad=Approval(approval.original_sha256,approval.final_sha256,approval.identity,(0xe6000,),approval.immutable_backup)
    with pytest.raises(bridge.ftr.fu.SafetyError):check_plan(bridge.ftr,plan,bad)


def test_manifest_package_is_fixed_to_verified_v15(tmp_path):
    p=tmp_path/'approval.json'
    p.write_text(json.dumps({'format':'fm1-stock-v15-application-approval-v1','package_sha256':'wrong'}))
    with pytest.raises(ValueError):read_approval(p)
