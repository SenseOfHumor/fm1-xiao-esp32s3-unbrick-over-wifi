"""Serial-compatible authenticated FM1W framed transport. Never reconnect/replay automatically."""
import socket
import struct
import time
import zlib

HEADER = struct.Struct('!4sIII')
MAX_FRAME = 4096

class TransportError(OSError):
    pass

def encode_frame(seq, payload):
    if not 0 < len(payload) <= MAX_FRAME:
        raise TransportError('invalid frame length')
    return HEADER.pack(b'FM1W', seq, len(payload), zlib.crc32(payload)) + payload

def recv_exact(sock, size, deadline):
    out = bytearray()
    while len(out) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TransportError('frame deadline expired')
        sock.settimeout(remaining)
        part = sock.recv(size - len(out))
        if not part:
            raise TransportError('connection lost; operation outcome may be unknown; do not replay writes')
        out.extend(part)
    return bytes(out)

def recv_frame(sock, seq, timeout):
    deadline = time.monotonic() + timeout
    magic, got_seq, n, crc = HEADER.unpack(recv_exact(sock, HEADER.size, deadline))
    if magic != b'FM1W' or got_seq != seq or not 0 < n <= MAX_FRAME:
        raise TransportError('invalid frame header or sequence')
    data = recv_exact(sock, n, deadline)
    if zlib.crc32(data) != crc:
        raise TransportError('frame CRC mismatch')
    return data

class TcpTransport:
    def __init__(self, host, secret, port=3333, timeout=5):
        self.timeout = timeout
        self.buffer = bytearray()
        self.wire_buffer = bytearray()
        self.frame_started = None
        self.tx = self.rx = 0
        self.sock = socket.create_connection((host, port), timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            self.write(secret.encode('ascii'))
            if self.readline() != b'AUTH OK\n':
                raise TransportError('authentication failed')
        except BaseException:
            self.close()
            raise

    def write(self, data):
        try:
            self.sock.settimeout(self.timeout)
            for off in range(0, len(data), MAX_FRAME):
                self.sock.sendall(encode_frame(self.tx, data[off:off+MAX_FRAME]))
                self.tx += 1
        except OSError:
            self.close()
            raise
        return len(data)

    def _receive(self, deadline):
        """Return False on a quiet serial-style poll; retain partial wire frames."""
        try:
            while True:
                if self.frame_started is not None and time.monotonic()-self.frame_started > 5:
                    raise TransportError('partial frame deadline expired')
                if len(self.wire_buffer) >= HEADER.size:
                    magic, seq, n, crc = HEADER.unpack(self.wire_buffer[:HEADER.size])
                    if magic != b'FM1W' or seq != self.rx or not 0 < n <= MAX_FRAME:
                        raise TransportError('invalid frame header or sequence')
                    if len(self.wire_buffer) >= HEADER.size+n:
                        data = bytes(self.wire_buffer[HEADER.size:HEADER.size+n])
                        if zlib.crc32(data) != crc:
                            raise TransportError('frame CRC mismatch')
                        del self.wire_buffer[:HEADER.size+n]
                        self.frame_started = time.monotonic() if self.wire_buffer else None
                        self.rx += 1
                        self.buffer.extend(data)
                        return True
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    return False
                if self.frame_started is not None:
                    remaining = min(remaining, 5-(time.monotonic()-self.frame_started))
                self.sock.settimeout(max(remaining, 0.001))
                try:
                    part = self.sock.recv(MAX_FRAME+HEADER.size)
                except socket.timeout:
                    continue
                if not part:
                    raise TransportError('connection lost; operation outcome may be unknown; do not replay writes')
                if not self.wire_buffer:
                    self.frame_started = time.monotonic()
                self.wire_buffer.extend(part)
        except OSError:
            self.close()
            raise

    def read(self, size=1):
        deadline = time.monotonic()+self.timeout
        while len(self.buffer) < size:
            if not self._receive(deadline):
                break
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        return data

    def readline(self):
        deadline = time.monotonic()+self.timeout
        while b'\n' not in self.buffer:
            if len(self.buffer) > 16384:
                self.close()
                raise TransportError('response line too long')
            if not self._receive(deadline):
                return b''
        n = self.buffer.index(b'\n')+1
        data = bytes(self.buffer[:n])
        del self.buffer[:n]
        return data

    def reset_input_buffer(self):
        # Do not discard bytes from partially received frames or reset sequence counters.
        self.buffer.clear()

    def close(self):
        self.sock.close()
