import struct
from utils import checksum


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
