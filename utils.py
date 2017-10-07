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

HELLO_HOLD_TIME_NO_TIMEOUT = 0xFFFF
HELLO_HOLD_TIME = 160
HELLO_HOLD_TIME_TIMEOUT = 0


def checksum(pkt: bytes) -> bytes:
    if len(pkt) % 2 == 1:
        pkt += "\0"
    s = sum(array.array("H", pkt))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    s = ~s
    return (((s >> 8) & 0xff) | s << 8) & 0xffff


import ctypes
import ctypes.util

libc = ctypes.CDLL(ctypes.util.find_library('c'))


def if_nametoindex(name):
    if not isinstance(name, str):
        raise TypeError('name must be a string.')
    ret = libc.if_nametoindex(name)
    if not ret:
        raise RuntimeError("Invalid Name")
    return ret


def if_indextoname(index):
    if not isinstance(index, int):
        raise TypeError('index must be an int.')
    libc.if_indextoname.argtypes = [ctypes.c_uint32, ctypes.c_char_p]
    libc.if_indextoname.restype = ctypes.c_char_p

    ifname = ctypes.create_string_buffer(32)
    ifname = libc.if_indextoname(index, ifname)
    if not ifname:
        raise RuntimeError ("Inavlid Index")
    return ifname.decode("utf-8")



# obtain TYPE_CHECKING (for type hinting)
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False


# IGMP timers (in seconds)
RobustnessVariable = 2
QueryInterval = 125
QueryResponseInterval = 10
MaxResponseTime_QueryResponseInterval = QueryResponseInterval*10
GroupMembershipInterval = RobustnessVariable * QueryInterval + QueryResponseInterval
OtherQuerierPresentInterval = RobustnessVariable * QueryInterval + QueryResponseInterval/2
StartupQueryInterval = QueryInterval / 4
StartupQueryCount = RobustnessVariable
LastMemberQueryInterval = 1
MaxResponseTime_LastMemberQueryInterval = LastMemberQueryInterval*10
LastMemberQueryCount = RobustnessVariable
UnsolicitedReportInterval = 10
Version1RouterPresentTimeout = 400

# IGMP msg type
Membership_Query = 0x11
Version_1_Membership_Report = 0x12
Version_2_Membership_Report = 0x16
Leave_Group = 0x17

