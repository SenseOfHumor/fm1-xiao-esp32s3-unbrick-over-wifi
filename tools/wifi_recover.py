#!/usr/bin/env python3
"""Run the pinned upstream recovery client over authenticated Wi-Fi frames."""
import argparse
import json
import sys
import time
from pathlib import Path
from tcp_transport import TcpTransport
from backup_safety import install_dump_capture, validate_reference
import esp32_recover as bridge

def wait_for_rom(t, wait):
    """Treat zero flags as a snapshot, not a terminal result or a reset request."""
    deadline = time.monotonic()+max(0, wait)
    t.send('status')
    next_ping = time.monotonic()+15
    bridge.ftr.log.info('Waiting up to %g s for real UBOOT readiness ...', wait)
    while True:
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise bridge.ftr.TransporterError('ROM readiness timed out after %g s; no reset or write performed' % wait)
        reply = t._readline(min(.5, remaining))
        if reply.startswith('ERR'):
            raise bridge.ftr.TransporterError('status: '+reply)
        if reply.startswith('OK '):
            st = bridge.ftr.parse_status(reply)
            if st.get('uboot') not in ('0', '1') or st.get('v15') not in ('0', '1'):
                raise bridge.ftr.TransporterError('invalid status flags: '+reply)
            if st['uboot'] == '1':
                return st  # ready() immediately follows this with checked info, no extra delay
            if st['v15'] == '1':
                raise bridge.ftr.TransporterError('application is mounted, not ROM; no soft-key/reset sent')
            bridge.ftr.log.debug('Not ready yet: %s', reply)
            remaining = deadline-time.monotonic()
            if remaining > 0:
                time.sleep(min(.1, remaining))
                t.send('status')  # previous request completed; never queue duplicate pending status
                next_ping = time.monotonic()+15
        elif reply and reply != 'PONG':
            raise bridge.ftr.TransporterError('unexpected status response: '+reply)
        # Old firmware can hold a status request throughout USB_KEY/host startup.
        # ping is handled independently by its RX task and keeps the TCP idle lease alive.
        if time.monotonic() >= next_ping:
            t.send('ping')
            next_ping = time.monotonic()+15


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--credentials', type=Path, default=Path(__file__).resolve().parents[1]/'wifi_credentials.json')
    parser.add_argument('--approved-v15', action='store_true')
    parser.add_argument('--approval-plan', type=Path)
    parser.add_argument('--evidence-dir', type=Path)
    parser.add_argument('--host')
    parser.add_argument('--tcp-port', type=int)
    opts, rest = parser.parse_known_args(argv)
    if opts.approval_plan and not opts.approved_v15:
        parser.error('--approval-plan requires an explicit --approved-v15 write approval')
    credentials = json.loads(opts.credentials.read_text())
    host = opts.host or credentials['host']
    port = opts.tcp_port or credentials['port']
    def connect():
        return TcpTransport(host, credentials['secret'], port)
    if rest[:1] in (['ping'], ['log'], ['selftest']):
        return diagnostics(rest[0], connect)
    # Same high-level package, identity, dump, reference and sector-safety logic.
    # No discovery over unrelated serial interfaces.
    bridge.ftr.candidate_ports = lambda: ['wifi']
    bridge.ftr.open_port = lambda _: bridge.ftr.Transporter(connect(), f'{host}:{port}')
    command=next((a for a in rest if a in ('wizard','flash-xiao','setup','recover','info','dump','restore','analyse','rekey','status')),None)
    if command in ('wizard', 'flash-xiao', 'setup', 'recover'):
        parser.error('use info, dump, or restore; guided automatic writes are disabled')
    if '--write' in rest and not opts.approved_v15:
        parser.error('FM-1 writes remain disabled pending an explicitly approved hardware dry-run')
    # In the upstream tool restore is a dry-run unless --write is given.
    if command == 'restore' and '--dry-run' in rest and '--mock-flash' not in rest:
        rest.remove('--dry-run')
    bridge.ftr.wait_status = wait_for_rom
    install_dump_capture(bridge.ftr)
    if command == 'restore':
        if '--ref' not in rest:
            parser.error('restore requires --ref and two preserved matching flash reads')
        validate_reference(rest[rest.index('--ref')+1], allow_mock='--mock-flash' in rest)
    if opts.approved_v15:
        if opts.evidence_dir is None:
            parser.error('--approved-v15 requires --evidence-dir')
        from approved_v15 import install
        install(bridge.ftr, rest, opts.evidence_dir, opts.approval_plan)
    return bridge.ftr.main(rest)

def diagnostics(command, connect):
    import hashlib
    import os
    s=connect()
    try:
        if command == 'ping':
            s.write(b'ping\n'); print(s.readline().decode().strip())
        elif command == 'log':
            s.write(b'log\n')
            line=s.readline()
            if not line.startswith(b'LOG '): raise RuntimeError(line)
            print(s.read(int(line.split()[1])).decode(),end='')
            if s.readline()!=b'END\n': raise RuntimeError('missing END')
        else:
            for size in (64,512,4096,65536,1048576):
                data=os.urandom(size)
                got=bytearray()
                # Frame marker 0 selects a harmless echo rather than the command parser.
                for off in range(0,size,4095):
                    chunk=data[off:off+4095]
                    s.write(b'\0'+chunk)
                    if s.read(1)!=b'\0': raise RuntimeError('echo marker')
                    got.extend(s.read(len(chunk)))
                if got!=data: raise RuntimeError('echo differs')
                print(size,hashlib.sha256(got).hexdigest(),'PASS')
    finally: s.close()
    if command=='selftest':
        s=connect()
        try:
            s.write(b'ping\n')
            if s.readline()!=b'PONG\n': raise RuntimeError('reconnection failed')
            print('reconnection PASS')
        finally: s.close()
    return 0

if __name__=='__main__':
    sys.exit(main())
