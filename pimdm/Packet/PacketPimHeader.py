import struct

from .PacketPimHello import PacketPimHello
from .PacketPimJoinPrune import PacketPimJoinPrune
from .PacketPimAssert import PacketPimAssert
from .PacketPimGraft import PacketPimGraft
from .PacketPimGraftAck import PacketPimGraftAck
from .PacketPimStateRefresh import PacketPimStateRefresh


from pimdm.utils import checksum
from .PacketPayload import PacketPayload
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|PIM Ver| Type  |   Reserved    |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketPimHeader(PacketPayload):
    PIM_VERSION = 2

    PIM_HDR = "! BB H"
    PIM_HDR_LEN = struct.calcsize(PIM_HDR)

    PIM_MSG_TYPES = {0: PacketPimHello,
                     3: PacketPimJoinPrune,
                     5: PacketPimAssert,
                     6: PacketPimGraft,
                     7: PacketPimGraftAck,
                     9: PacketPimStateRefresh
                     }

    def __init__(self, payload):
        self.payload = payload

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
        if checksum(msg_to_checksum) != rcv_checksum:
            print("wrong checksum")
            print("checksum calculated: " + str(checksum(msg_to_checksum)))
            print("checksum recv: " + str(rcv_checksum))
            raise Exception

        pim_payload = data[PacketPimHeader.PIM_HDR_LEN:]
        pim_payload = PacketPimHeader.PIM_MSG_TYPES[pim_type].parse_bytes(pim_payload)
        return PacketPimHeader(pim_payload)
