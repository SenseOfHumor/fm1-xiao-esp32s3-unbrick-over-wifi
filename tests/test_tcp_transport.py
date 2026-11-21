import hashlib
import socket
import struct
import sys
import threading
import time
import zlib
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from tcp_transport import TcpTransport, TransportError, encode_frame, recv_frame

class Fragmented:
    def __init__(self,data): self.data=bytearray(data)
    def settimeout(self,n): pass
    def recv(self,n):
        data=bytes(self.data[:min(n,3)]); del self.data[:len(data)]; return data

@pytest.mark.parametrize('size',[64,512,4096])
def test_partial_reads(size):
    data=bytes(i%256 for i in range(size))
    assert recv_frame(Fragmented(encode_frame(12,data)),12,1)==data

@pytest.mark.parametrize('header',[struct.pack('!4sIII',b'NOPE',0,1,0),struct.pack('!4sIII',b'FM1W',2,1,0),struct.pack('!4sIII',b'FM1W',0,4097,0),struct.pack('!4sIII',b'FM1W',0,0,0)])
def test_bad_headers(header):
    with pytest.raises(TransportError): recv_frame(Fragmented(header),0,1)

def test_crc():
    data=bytearray(encode_frame(0,b'test'));data[-1]^=1
    with pytest.raises(TransportError,match='CRC'): recv_frame(Fragmented(data),0,1)

def test_truncated_connection():
    with pytest.raises(TransportError,match='connection lost'): recv_frame(Fragmented(encode_frame(0,b'payload')[:-1]),0,1)

def test_deadline():
    with pytest.raises(TransportError,match='deadline'): recv_frame(Fragmented(b''),0,0)

@pytest.fixture
def echo_server():
    listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen()
    errors=[]
    def server():
        try:
            for _ in range(2):
                conn,_=listener.accept()
                with conn:
                    if recv_frame(conn,0,1)!=b'secret': continue
                    conn.sendall(encode_frame(0,b'AUTH OK\n'))
                    seq=1
                    while True:
                        try: payload=recv_frame(conn,seq,2)
                        except (OSError,TransportError): break
                        conn.sendall(encode_frame(seq,payload)); seq+=1
        except Exception as e: errors.append(e)
    thread=threading.Thread(target=server,daemon=True);thread.start()
    yield listener.getsockname()[1]
    listener.close();thread.join(timeout=3)
    assert not errors

@pytest.mark.parametrize('size',[64,512,4096,65536,1048576])
def test_binary_and_reconnection(echo_server,size):
    data=bytes(i%251 for i in range(size))
    for _ in range(2):
        s=TcpTransport('127.0.0.1','secret',echo_server)
        out=bytearray()
        for off in range(0,len(data),4096):
            chunk=data[off:off+4096];s.write(chunk);out.extend(s.read(len(chunk)))
        assert hashlib.sha256(out).digest()==hashlib.sha256(data).digest()
        s.close()

def test_auth_rejected(echo_server):
    with pytest.raises(TransportError): TcpTransport('127.0.0.1','wrong',echo_server)
    s=TcpTransport('127.0.0.1','secret',echo_server);s.close()

@pytest.mark.parametrize('split',[0,7,18])
def test_serial_polls_preserve_delayed_status_and_partial_frames(split):
    """Real upstream wait_status polls every .5s; silence is not a lost TCP link."""
    import esp32_recover as bridge
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen()
    errors=[]
    def serve():
        try:
            conn,_=listener.accept()
            with conn:
                assert recv_frame(conn,0,2)==b'secret'
                conn.sendall(encode_frame(0,b'AUTH OK\n'))
                assert recv_frame(conn,1,2)==b'status\n'
                reply=encode_frame(1,b'OK uboot=1 v15=0 loader=1 loader_running=0\n')
                if split:conn.sendall(reply[:split])
                time.sleep(.7)
                conn.sendall(reply[split:])
                time.sleep(.1)
        except BaseException as e:errors.append(e)
    thread=threading.Thread(target=serve);thread.start()
    s=TcpTransport('127.0.0.1','secret',listener.getsockname()[1])
    try:
        t=bridge.ftr.Transporter(s,'local TCP regression test')
        assert bridge.ftr.wait_status(t,2)['uboot']=='1'
    finally:
        s.close();thread.join(3);listener.close()
    assert not thread.is_alive()
    assert not errors
