import struct


class PacketIpHeader:
    IP_HDR = "! BBH HH BBH 4s 4s"
    #IP_HDR2 = "! B"
    IP_HDR_LEN = struct.calcsize(IP_HDR)

    def __init__(self, ip):
        self.ip = ip
