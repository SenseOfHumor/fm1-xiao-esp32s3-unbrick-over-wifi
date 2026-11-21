#!/usr/bin/env python3
"""Create private credentials once; never rotate an existing board accidentally."""
import argparse
import datetime
import json
import secrets
import shutil
from pathlib import Path


def generate(root, rotate=False):
    root = Path(root)
    paths = [root / 'wifi_credentials.json', root / 'sdkconfig.wifi']
    if any(p.exists() for p in paths):
        if not rotate:
            raise FileExistsError('credentials already exist; preserve them or explicitly use --rotate')
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        for path in paths:
            if path.exists():
                backup = path.with_name(path.name + '.' + stamp + '.backup')
                shutil.copy2(path, backup)
                backup.chmod(0o600)
    creds = dict(ssid='FM1-Recovery', password=secrets.token_hex(8),
                 secret=secrets.token_hex(24), host='192.168.4.1', port=3333)
    for path in paths:
        path.touch(mode=0o600)
        path.chmod(0o600)
    paths[0].write_text(json.dumps(creds, indent=2) + '\n')
    paths[1].write_text('CONFIG_FM1_AP_PASSWORD="%s"\nCONFIG_FM1_SESSION_SECRET="%s"\n'
                        % (creds['password'], creds['secret']))
    return creds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rotate', action='store_true', help='back up old credentials and deliberately replace them; rebuild/reflash needed')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    generate(root, args.rotate)
    print('Private credentials saved to', root / 'wifi_credentials.json')
    print('Existing sdkconfig files retain old values: see docs/BUILD_AND_FLASH.md before rotating.')


if __name__ == '__main__':
    main()
