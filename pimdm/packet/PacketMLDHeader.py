import struct
import socket
from .PacketPayload import PacketPayload

"""
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Type      |     Code      |          Checksum             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Maximum Response Delay    |          Reserved             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                       Multicast Address                       +
|                                                               |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""
class PacketMLDHeader(PacketPayload):
    MLD_TYPE = 58

    MLD_HDR = "! BB H H H 16s"
    MLD_HDR_LEN = struct.calcsize(MLD_HDR)

    MULTICAST_LISTENER_QUERY_TYPE = 130
    MULTICAST_LISTENER_REPORT_TYPE = 131
    MULTICAST_LISTENER_DONE_TYPE = 132

    def __init__(self, type: int, max_resp_delay: int, group_address: str = "::"):
        # todo check type
        self.type = type
        self.max_resp_delay = max_resp_delay
        self.group_address = group_address

    def get_mld_type(self):
        return self.type

    def bytes(self) -> bytes:
        # obter mensagem e criar checksum
        msg_without_chcksum = struct.pack(PacketMLDHeader.MLD_HDR, self.type, 0, 0, self.max_resp_delay, 0,
                                          socket.inet_pton(socket.AF_INET6, self.group_address))
        #mld_checksum = checksum(msg_without_chcksum)
        #msg = msg_without_chcksum[0:2] + struct.pack("! H", mld_checksum) + msg_without_chcksum[4:]
        # checksum handled by linux kernel
        return msg_without_chcksum

    def __len__(self):
        return len(self.bytes())


    @staticmethod
    def parse_bytes(data: bytes):
        mld_hdr = data[0:PacketMLDHeader.MLD_HDR_LEN]
        if len(mld_hdr) < PacketMLDHeader.MLD_HDR_LEN:
            raise Exception("MLD packet length is lower than expected")
        (mld_type, _, _, max_resp_delay, _, group_address) = struct.unpack(PacketMLDHeader.MLD_HDR, mld_hdr)
        # checksum is handled by linux kernel
        mld_hdr = mld_hdr[PacketMLDHeader.MLD_HDR_LEN:]
        group_address = socket.inet_ntop(socket.AF_INET6, group_address)
        pkt = PacketMLDHeader(mld_type, max_resp_delay, group_address)
        return pkt
