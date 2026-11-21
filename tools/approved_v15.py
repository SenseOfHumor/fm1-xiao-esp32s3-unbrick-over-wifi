"""Strict, snapshot-bound approval for application-only stock V15 restoration.

The historical defaults preserve the successful 2026-11-21 recovery. Other
units must use an explicitly reviewed plan from prepare_v15_plan.py.
"""
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from backup_safety import validate_reference

ORIGINAL = '68c5c500ed28aa73b6d9ece9ba8e12795a4985625fa76c77e66d28cfdf3ddea2'
PACKAGE = 'db1642b2b6fa5c2cccb11ffd13878068bb28601678d3644049f99dc40e7edb8a'
FINAL = '872d9c4c7ccce4520ba94bbc60c3d4dbc43abfee77ce686f79aa510c66f02b79'
IDENTITY = 'OK key=980F type=3 id=856014'
SECTORS = list(range(0x4000, 0x93000, 0x1000))


def sha(data):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Approval:
    original_sha256: str
    final_sha256: str
    identity: str
    sectors: tuple
    immutable_backup: Path


def historical_approval():
    return Approval(ORIGINAL, FINAL, IDENTITY, tuple(SECTORS),
                    Path.home() / 'Documents/FM1_BACKUPS' / ('fm1-original-' + ORIGINAL + '.bin'))


def read_approval(path):
    data = json.loads(Path(path).read_text())
    if data.get('format') != 'fm1-stock-v15-application-approval-v1' or data.get('package_sha256') != PACKAGE:
        raise ValueError('unsupported approval format or unverified V15 package')
    return Approval(data['original_sha256'], data['final_sha256'], data['identity'],
                    tuple(int(a, 0) for a in data['sectors']), Path(data['immutable_backup']).resolve())


def verify_immutable_copy(approval):
    path = approval.immutable_backup
    if sha(path.read_bytes()) != approval.original_sha256:
        raise ValueError('independent original copy hash mismatch')
    info = path.stat()
    if hasattr(info, 'st_flags') and hasattr(stat, 'UF_IMMUTABLE'):
        if not info.st_flags & stat.UF_IMMUTABLE:
            raise ValueError('macOS independent backup must have the uchg immutable flag')
    elif info.st_mode & 0o222:
        raise ValueError('independent original copy must be read-only')


def check_plan(ftr, plan, approval=None):
    approval = approval or historical_approval()
    if (sha(plan.ref) != approval.original_sha256 or plan.pkg.file_sha256 != PACKAGE
            or plan.pkg.kind != 'official-v15'):
        raise ftr.fu.SafetyError('original/V15 package differs from the reviewed approval')
    supported = {'OK key=980F type=3 id=' + fid for fid in ftr.IDS_OK}
    if approval.identity not in supported:
        raise ftr.fu.SafetyError('approval has an unsupported hardware identity')
    if (plan.head_diff or tuple(plan.write) != approval.sectors or not plan.write
            or any(a < 0x4000 or a >= 0x93000 or a % 4096 for a in plan.write)):
        raise ftr.fu.SafetyError('sector plan differs from the exact application-only approval')
    expected = plan.ref[:0x4000] + plan.img[0x4000:0x93000] + plan.ref[0x93000:]
    if sha(expected) != approval.final_sha256:
        raise ftr.fu.SafetyError('approved expected-image hash mismatch')
    return expected


def install(ftr, argv, evidence, approval_path=None):
    args = ftr.build_parser().parse_args(argv)
    if (args.command != 'restore' or not args.write or not args.verify_v15
            or args.dry_run or args.image or args.mock_flash):
        raise ftr.fu.SafetyError('--approved-v15 requires real restore --write --verify-v15, package and --ref')
    approval = read_approval(approval_path) if approval_path else historical_approval()
    if validate_reference(args.ref) != approval.original_sha256:
        raise ftr.fu.SafetyError('original independent backups do not match approval')
    verify_immutable_copy(approval)
    pkg = ftr.load_restore_package(args.package, True)
    plan = ftr.Plan(pkg, Path(args.ref).read_bytes(), Path(args.ref))
    check_plan(ftr, plan, approval)
    out = Path(evidence).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any((out / n).exists() for n in ('write-journal.jsonl', 'fresh-read.bin',
                                       'final-read.bin', 'RESTORE_VERIFIED.json')):
        raise ftr.fu.SafetyError('choose new evidence directory; never overwrite a prior write journal')
    original = ftr.restore_session

    def guarded(t, plan, args, write, confirm=None):
        expected = check_plan(ftr, plan, approval)
        if not write or t.mock:
            raise ftr.fu.SafetyError('approved execution must be a real write session')
        proxy = ApprovedTransport(t, ftr, plan, expected, out, approval)
        result = original(proxy, plan, args, write, confirm)
        if result == 0:
            if tuple(proxy.completed) != approval.sectors or not proxy.final_verified:
                raise ftr.fu.SafetyError('missing sector acknowledgments/final full verification')
            marker = dict(original_sha256=approval.original_sha256, package_sha256=PACKAGE,
                          final_sha256=approval.final_sha256, identity=approval.identity,
                          verified_sectors=len(proxy.completed), protected_regions_unchanged=True)
            with (out / 'RESTORE_VERIFIED.json').open('x') as f:
                json.dump(marker, f, indent=2)
                f.write('\n')
                f.flush()
                os.fsync(f.fileno())
        return result

    ftr.restore_session = guarded


class ApprovedTransport:
    def __init__(self, t, ftr, plan, expected, out, approval=None):
        self.t, self.ftr, self.plan, self.expected, self.out = t, ftr, plan, expected, out
        self.approval = approval or historical_approval()
        self.fresh_verified = False
        self.final_verified = False
        self.completed = []

    def __getattr__(self, name):
        return getattr(self.t, name)

    def info(self):
        reply = self.t.info()
        if reply != self.approval.identity:
            raise self.ftr.fu.SafetyError('actual live identity differs from approval: ' + reply)
        return reply

    def read_flash(self, addr, length, label='Reading'):
        data = self.t.read_flash(addr, length, label)
        if addr == 0 and length == 0x100000:
            if not self.fresh_verified:
                if data != self.plan.ref:
                    raise self.ftr.fu.SafetyError('fresh full flash differs from original, including protected data; no writes allowed')
                self._save('fresh-read.bin', data)
                self.fresh_verified = True
            else:
                self._save('final-read.bin', data)
                if data != self.expected:
                    raise self.ftr.fu.SafetyError('final full-image verification FAILED; keep devices powered')
                self.final_verified = True
        return data

    def _save(self, name, data):
        with (self.out / name).open('xb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

    def _journal(self, state, addr):
        with (self.out / 'write-journal.jsonl').open('a') as f:
            f.write(json.dumps(dict(state=state, address='0x%05X' % addr)) + '\n')
            f.flush()
            os.fsync(f.fileno())

    def write_sector(self, addr, data):
        index = len(self.completed)
        if (not self.fresh_verified or index >= len(self.approval.sectors)
                or addr != self.approval.sectors[index] or len(data) != 4096
                or data != self.expected[addr:addr + 4096]):
            raise self.ftr.fu.SafetyError('sector operation is outside the exact approved sequence/payload')
        self._journal('STARTED', addr)
        reply = self.t.write_sector(addr, data)
        if reply == 'OK':
            self.completed.append(addr)
            self._journal('VERIFIED', addr)
        else:
            self._journal('FAILED_UNKNOWN', addr)
        return reply
