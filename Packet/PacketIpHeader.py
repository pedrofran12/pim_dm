import struct


class PacketIpHeader:
    IP_HDR = "! BBH HH BBH LL"
    #IP_HDR2 = "! B"
    IP_HDR_LEN = struct.calcsize(IP_HDR)

    def __init__(self, ip):
        self.ip = ip
