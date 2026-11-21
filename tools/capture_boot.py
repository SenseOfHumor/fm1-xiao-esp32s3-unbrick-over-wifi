#!/usr/bin/env python3
import sys
import time
import serial
s=serial.Serial()
s.port=sys.argv[1]
s.baudrate=115200
s.timeout=0.2
s.dtr=False
s.rts=False
s.open()
end=time.monotonic()+(float(sys.argv[2]) if len(sys.argv)>2 else 30)
with open('logs/xiao-boot.log','ab') as out:
    while time.monotonic()<end:
        data=s.read(4096)
        if data: out.write(data);out.flush()
s.close()
