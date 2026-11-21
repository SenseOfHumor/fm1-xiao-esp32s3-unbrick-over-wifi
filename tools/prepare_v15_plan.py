#!/usr/bin/env python3
"""Create a reviewable OFFLINE V15 approval plan; never contacts hardware."""
import argparse
import json
import os
import stat
from pathlib import Path
from approved_v15 import PACKAGE, Approval, check_plan, sha, verify_immutable_copy
from backup_safety import validate_reference
import esp32_recover as bridge


def prepare(backup_dir, package, immutable_backup, output):
    backup_dir, immutable_backup, output = map(Path, (backup_dir, immutable_backup, output))
    ref_path = backup_dir / 'full-flash-before-1.bin'
    original_sha = validate_reference(ref_path)
    metadata = json.loads((backup_dir / 'analysis.json').read_text())
    identity = metadata['identity']
    identity_line = 'OK key=%s type=%s id=%s' % (identity['key'], identity['type'], identity['id'])
    data = ref_path.read_bytes()
    pkg = bridge.ftr.load_restore_package(package, True)
    if pkg.file_sha256 != PACKAGE:
        raise ValueError('package file is not the exact verified public V15')
    plan = bridge.ftr.Plan(pkg, data, ref_path)
    if plan.head_diff:
        raise ValueError('head differs from public V15; stop for independent review')
    if not plan.write:
        raise ValueError('application already equals V15; no firmware write is needed')
    expected = data[:0x4000] + pkg.firmware + data[0x93000:]
    approval = Approval(original_sha, sha(expected), identity_line, tuple(plan.write), immutable_backup.resolve())
    check_plan(bridge.ftr, plan, approval)
    if immutable_backup.resolve() in {ref_path.resolve(), (backup_dir / 'full-flash-before-2.bin').resolve()}:
        raise ValueError('independent copy must be distinct from both source reads')
    immutable_backup.parent.mkdir(parents=True, exist_ok=True)
    if not immutable_backup.exists():
        with immutable_backup.open('xb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        immutable_backup.chmod(0o400)
        if hasattr(os, 'chflags') and hasattr(stat, 'UF_IMMUTABLE'):
            os.chflags(immutable_backup, immutable_backup.stat().st_flags | stat.UF_IMMUTABLE)
    verify_immutable_copy(approval)
    result = dict(format='fm1-stock-v15-application-approval-v1',
                  notice='OFFLINE PLAN ONLY. Review and explicitly approve before --approved-v15.',
                  original_sha256=original_sha, final_sha256=sha(expected),
                  package_sha256=PACKAGE, identity=identity_line,
                  immutable_backup=str(approval.immutable_backup),
                  sectors=['0x%05X' % a for a in plan.write],
                  protected=['0x00000..0x03FFF', '0x93000..0xFFFFF'],
                  sector_count=len(plan.write), program_bytes=len(plan.write)*4096)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print('OFFLINE ONLY: no device contacted; creating this file does not authorize a write.')
    print('Plan:', output)
    print('Identity:', identity_line)
    print('Erase/program %d sectors inside 0x04000..0x92FFF:' % len(plan.write))
    for a in plan.write:
        print('  0x%05X..0x%05X' % (a, a+4095))
    print('Expected full-image SHA256:', sha(expected))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backup-dir', type=Path, required=True)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--immutable-backup', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    prepare(args.backup_dir, args.package, args.immutable_backup, args.out)


if __name__ == '__main__':
    main()
