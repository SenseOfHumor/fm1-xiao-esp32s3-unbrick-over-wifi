"""Compile the firmware's actual portable codec and compare it with Python."""
import ctypes
import subprocess
from pathlib import Path
import pytest
from tcp_transport import encode_frame

@pytest.fixture(scope='module')
def codec(tmp_path_factory):
    root=Path(__file__).resolve().parents[1]
    dest=tmp_path_factory.mktemp('codec')/'wire.dylib'
    subprocess.run(['cc','-shared','-fPIC','-Wall','-Werror',str(root/'main/wire_protocol.c'),'-o',str(dest)],check=True)
    lib=ctypes.CDLL(str(dest))
    lib.fm1_frame_header.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32]
    lib.fm1_frame_parse.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint32)]
    lib.fm1_frame_parse.restype=ctypes.c_bool
    return lib

@pytest.mark.parametrize('size',[1,64,512,4096])
def test_firmware_codec(codec,size):
    data=bytes(i%251 for i in range(size));h=ctypes.create_string_buffer(16)
    codec.fm1_frame_header(h,17,data,size)
    assert h.raw==encode_frame(17,data)[:16]
    n=ctypes.c_uint32();crc=ctypes.c_uint32()
    assert codec.fm1_frame_parse(h,17,ctypes.byref(n),ctypes.byref(crc))
    assert n.value==size
    assert not codec.fm1_frame_parse(h,18,ctypes.byref(n),ctypes.byref(crc))

@pytest.mark.parametrize('size',[0,4097,0xffffffff])
def test_firmware_length_rejection(codec,size):
    import struct
    h=struct.pack('!4sIII',b'FM1W',0,size,0)
    n=ctypes.c_uint32();crc=ctypes.c_uint32()
    assert not codec.fm1_frame_parse(h,0,ctypes.byref(n),ctypes.byref(crc))
