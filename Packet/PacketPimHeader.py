import struct

from Packet.PacketPimHello import PacketPimHello
from Packet.PacketPimJoinPrune import PacketPimJoinPrune
from utils import checksum

'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|PIM Ver| Type  |   Reserved    |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketPimHeader:
    PIM_VERSION = 2

    PIM_HDR = "! BB H"
    PIM_HDR_LEN = struct.calcsize(PIM_HDR)

    def __init__(self, payload):
        self.payload = payload
        #self.msg_type = msg_type

    def get_pim_type(self):
        return self.payload.PIM_TYPE

    def bytes(self) -> bytes:
        # obter mensagem e criar checksum
        pim_vrs_type = (PacketPimHeader.PIM_VERSION << 4) + self.get_pim_type()
        msg_without_chcksum = struct.pack(PacketPimHeader.PIM_HDR, pim_vrs_type, 0, 0)
        msg_without_chcksum += self.payload.bytes()
        pim_checksum = checksum(msg_without_chcksum)
        msg = msg_without_chcksum[0:2] + struct.pack("! H", pim_checksum) + msg_without_chcksum[4:]
        return msg

    def __len__(self):
        return len(self.bytes())

    @staticmethod
    def parse_bytes(data: bytes):
        print("parsePimHdr: ", data)

        pim_hdr = data[0:PacketPimHeader.PIM_HDR_LEN]
        (pim_ver_type, reserved, rcv_checksum) = struct.unpack(PacketPimHeader.PIM_HDR, pim_hdr)

        print(pim_ver_type, reserved, rcv_checksum)
        pim_version = (pim_ver_type & 0xF0) >> 4
        pim_type = pim_ver_type & 0x0F

        if pim_version != PacketPimHeader.PIM_VERSION:
            print("Version of PIM packet received not known (!=2)")
            raise Exception

        msg_to_checksum = data[0:2] + b'\x00\x00' + data[4:]
        print("checksum calculated: " + str(checksum(msg_to_checksum)))
        if checksum(msg_to_checksum) != rcv_checksum:
            print("wrong checksum")
            raise Exception

        pim_payload = data[PacketPimHeader.PIM_HDR_LEN:]
        if pim_type == 0:  # hello
            pim_payload = PacketPimHello.parse_bytes(pim_payload)
        elif pim_type == 3:  # join/prune
            pim_payload = PacketPimJoinPrune.parse_bytes(pim_payload)
            print("hold_time = ", pim_payload.hold_time)
            print("upstream_neighbor = ", pim_payload.upstream_neighbor_address)
            for i in pim_payload.groups:
                print(i.multicast_group)
                print(i.joined_src_addresses)
                print(i.pruned_src_addresses)

        else:
            raise Exception

        return PacketPimHeader(pim_payload)
