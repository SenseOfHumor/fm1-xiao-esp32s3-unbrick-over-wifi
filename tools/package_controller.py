#!/usr/bin/env python3
"""Create a PRIVATE controller ZIP: includes credentials and local V15, never publish it."""
import argparse
import datetime
import hashlib
import zipfile
from pathlib import Path
from approved_v15 import PACKAGE


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out = args.out or root / ('artifacts/controller-' + stamp + '.zip')
    if out.exists():
        raise FileExistsError('refusing to overwrite an existing controller archive')
    firmware = root / 'third_party/FM1Backups/V15-FM-1.fwsc'
    if hashlib.sha256(firmware.read_bytes()).hexdigest() != PACKAGE:
        raise ValueError('local V15 file does not match the verified package hash')
    paths = ['wifi_credentials.json', 'requirements.txt']
    paths += ['tools/' + n for n in ('wifi_recover.py', 'tcp_transport.py', 'esp32_recover.py',
                                     'backup_safety.py', 'approved_v15.py', 'prepare_v15_plan.py')]
    paths += ['third_party/MvaveFM1Unbricker/' + n for n in
              ('fm1_transporter_recover.py', 'fm1_unbrick.py', 'fm1_macusb.py')]
    paths += ['third_party/FM1Backups/V15-FM-1.fwsc']
    paths += [str(p.relative_to(root)) for p in (root / 'docs').glob('*.md')]
    paths += ['README.md', 'LICENSE']
    out.parent.mkdir(parents=True, exist_ok=True)
    out.touch(mode=0o600, exist_ok=False)
    out.chmod(0o600)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in paths:
            archive.write(root / name, 'fm1-controller/' + name)
        archive.writestr('fm1-controller/START_HERE.txt',
                        'PRIVATE: this ZIP contains Wi-Fi credentials and a firmware package.\n'
                        'Do not publish it. Read README.md and docs/REPRODUCING.md.\n'
                        'Install requirements.txt, manually join the board AP, then run\n'
                        'python tools/wifi_recover.py ping and log.\n'
                        'Use only your own verified backups and reviewed approval plan.\n')
    print(out)
    print(hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
