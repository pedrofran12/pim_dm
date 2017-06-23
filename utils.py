import array
'''
import struct
if struct.pack("H",1) == "\x00\x01": # big endian
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array.array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return s & 0xffff
else:
    def checksum(pkt):
        if len(pkt) % 2 == 1:
            pkt += "\0"
        s = sum(array.array("H", pkt))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        s = ~s
        return (((s>>8)&0xff)|s<<8) & 0xffff
'''

KEEP_ALIVE_PERIOD_NO_TIMEOUT = 0xFFFF
KEEP_ALIVE_PERIOD = 160
KEEP_ALIVE_PERIOD_TIMEOUT = 0


def checksum(pkt):
    if len(pkt) % 2 == 1:
        pkt += "\0"
    s = sum(array.array("H", pkt))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    s = ~s
    return (((s >> 8) & 0xff) | s << 8) & 0xffff

