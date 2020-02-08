import struct
from pimdm.utils import checksum
import socket
from .PacketPayload import PacketPayload
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|      Type     | Max Resp Time |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Group Address                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Resv  |S| QRV |     QQIC      |     Number of Sources (N)     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address [1]                      |
+-                                                             -+
|                       Source Address [2]                      |
+-                              .                              -+
.                               .                               .
.                               .                               .
+-                                                             -+
|                       Source Address [N]                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketIGMPHeader(PacketPayload):
    IGMP_TYPE = 2

    IGMP_HDR = "! BB H 4s"
    IGMP_HDR_LEN = struct.calcsize(IGMP_HDR)

    IGMP3_SRC_ADDR_HDR = "! BB H "
    IGMP3_SRC_ADDR_HDR_LEN = struct.calcsize(IGMP3_SRC_ADDR_HDR)

    IPv4_HDR = "! 4s"
    IPv4_HDR_LEN = struct.calcsize(IPv4_HDR)

    Membership_Query = 0x11
    Version_2_Membership_Report = 0x16
    Leave_Group = 0x17
    Version_1_Membership_Report = 0x12

    def __init__(self, type: int, max_resp_time: int, group_address: str="0.0.0.0"):
        # todo check type
        self.type = type
        self.max_resp_time = max_resp_time
        self.group_address = group_address

    def get_igmp_type(self):
        return self.type

    def bytes(self) -> bytes:
        # obter mensagem e criar checksum
        msg_without_chcksum = struct.pack(PacketIGMPHeader.IGMP_HDR, self.type, self.max_resp_time, 0,
                                          socket.inet_aton(self.group_address))
        igmp_checksum = checksum(msg_without_chcksum)
        msg = msg_without_chcksum[0:2] + struct.pack("! H", igmp_checksum) + msg_without_chcksum[4:]
        return msg

    def __len__(self):
        return len(self.bytes())

    @staticmethod
    def parse_bytes(data: bytes):
        #print("parseIGMPHdr: ", data)

        igmp_hdr = data[0:PacketIGMPHeader.IGMP_HDR_LEN]
        (type, max_resp_time, rcv_checksum, group_address) = struct.unpack(PacketIGMPHeader.IGMP_HDR, igmp_hdr)

        #print(type, max_resp_time, rcv_checksum, group_address)


        msg_to_checksum = data[0:2] + b'\x00\x00' + data[4:]
        #print("checksum calculated: " + str(checksum(msg_to_checksum)))
        if checksum(msg_to_checksum) != rcv_checksum:
            #print("wrong checksum")
            raise Exception("wrong checksum")

        igmp_hdr = igmp_hdr[PacketIGMPHeader.IGMP_HDR_LEN:]
        group_address = socket.inet_ntoa(group_address)
        pkt = PacketIGMPHeader(type, max_resp_time, group_address)
        return pkt