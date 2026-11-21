"""Readiness state regressions; no physical target, reset or flash command."""
import pytest
import wifi_recover as wifi

ZERO='OK uboot=0 v15=0 loader=1 loader_running=0'
READY='OK uboot=1 v15=0 loader=1 loader_running=0'

class Clock:
    def __init__(self):self.now=0
    def monotonic(self):return self.now
    def sleep(self,n):self.now+=n

class Link:
    def __init__(self,clock,replies):self.clock=clock;self.replies=iter(replies);self.sent=[]
    def send(self,line):self.sent.append(line)
    def _readline(self,timeout):
        self.clock.now+=timeout
        reply=next(self.replies,'')
        if isinstance(reply,Exception):raise reply
        return reply

@pytest.fixture
def clock(monkeypatch):
    c=Clock();monkeypatch.setattr(wifi,'time',c);return c

def test_zero_snapshots_wait_for_ready(clock):
    t=Link(clock,[ZERO,ZERO,READY])
    assert wifi.wait_for_rom(t,180)['uboot']=='1'
    assert t.sent==['status']*3

def test_status_can_wait_while_keying_without_duplicate_request(clock):
    t=Link(clock,['']*40+['PONG',READY])
    assert wifi.wait_for_rom(t,180)['uboot']=='1'
    assert t.sent==['status','ping']

def test_deadline_is_not_first_zero(clock):
    t=Link(clock,[ZERO]*400)
    with pytest.raises(wifi.bridge.ftr.TransporterError,match='timed out'):
        wifi.wait_for_rom(t,180)
    assert clock.now==pytest.approx(180)
    assert set(t.sent)=={'status'}

@pytest.mark.parametrize('reply',['ERR usb-recovery-disabled','ERR no-uboot','OK uboot=wat v15=0','garbage'])
def test_terminal_errors_stop(clock,reply):
    t=Link(clock,[reply])
    with pytest.raises(wifi.bridge.ftr.TransporterError):wifi.wait_for_rom(t,180)
    assert t.sent==['status']

def test_no_softkey_or_reset_on_application(clock):
    t=Link(clock,['OK uboot=0 v15=1 loader=1 loader_running=0'])
    with pytest.raises(wifi.bridge.ftr.TransporterError,match='no soft-key/reset'):
        wifi.wait_for_rom(t,180)
    assert t.sent==['status']

def test_disconnect_is_not_retried(clock):
    t=Link(clock,[OSError('connection lost')])
    with pytest.raises(OSError,match='connection lost'):wifi.wait_for_rom(t,180)
    assert t.sent==['status']

def test_ready_followed_immediately_by_checked_identity(clock):
    t=Link(clock,[ZERO,READY])
    t.info=lambda: t.sent.append('info') or 'OK key=980F type=3 id=856014'
    st=wifi.wait_for_rom(t,180)
    wifi.bridge.ftr.ensure_uboot(t,st)
    wifi.bridge.ftr.check_info(t)
    assert t.sent==['status','status','info']

def test_wifi_cli_installs_readiness_wait(monkeypatch,tmp_path):
    import json
    cfg=tmp_path/'credentials.json'
    cfg.write_text(json.dumps(dict(host='127.0.0.1',port=3333,secret='test secret')))
    monkeypatch.setattr(wifi,'install_dump_capture',lambda module:None)
    monkeypatch.setattr(wifi.bridge.ftr,'candidate_ports',wifi.bridge.ftr.candidate_ports)
    monkeypatch.setattr(wifi.bridge.ftr,'open_port',wifi.bridge.ftr.open_port)
    old=wifi.bridge.ftr.wait_status
    monkeypatch.setattr(wifi.bridge.ftr,'wait_status',old)
    monkeypatch.setattr(wifi.bridge.ftr,'main',lambda argv: int(wifi.bridge.ftr.wait_status is not wifi.wait_for_rom))
    assert wifi.main(['--credentials',str(cfg),'info','--wait','180'])==0


def test_framed_tcp_zero_then_ready_then_identity(monkeypatch):
    import socket,threading
    from types import SimpleNamespace
    from tcp_transport import TcpTransport,encode_frame,recv_frame
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen()
    seen=[];errors=[]
    def server():
        try:
            conn,_=listener.accept()
            with conn:
                assert recv_frame(conn,0,3)==b'secret'
                conn.sendall(encode_frame(0,b'AUTH OK\n'))
                for seq,expected,reply in [(1,b'status\n',ZERO),(2,b'status\n',READY),
                    (3,b'info\n','OK key=980F type=3 id=B36014')]:
                    command=recv_frame(conn,seq,3);seen.append(command)
                    assert command==expected
                    conn.sendall(encode_frame(seq,(reply+'\n').encode()))
        except BaseException as e:errors.append(e)
    thread=threading.Thread(target=server);thread.start()
    s=TcpTransport('127.0.0.1','secret',listener.getsockname()[1])
    monkeypatch.setattr(wifi.bridge.ftr,'wait_status',wifi.wait_for_rom)
    try:
        t=wifi.bridge.ftr.Transporter(s,'targeted TCP test')
        assert wifi.bridge.ftr.cmd_info(SimpleNamespace(wait=3),transporter=t)==0
    finally:
        s.close();thread.join(4);listener.close()
    assert not thread.is_alive()
    assert not errors
    assert seen==[b'status\n',b'status\n',b'info\n']
