import struct
from utils import checksum


class PacketPimHeader:
    PIM_VERSION = 2

    PIM_HDR = "! BB H"
    PIM_HDR_LEN = struct.calcsize(PIM_HDR)

    # HELLO: type = 0
    # pim options
    def __init__(self, msg_type):
        self.options = []
        self.msg_type = msg_type

    def add_option(self, option):
        self.options.append(option)

    def get_options_bytes(self):
        res = b''
        #print(self.options[0].option_type)
        self.options.sort(key=lambda x: x.option_type)  # TODO: duvida... ordenar? maybe not
        #print(self.options[0].option_type)
        for opt in self.options:
            res += opt.bytes()
        return res

    def get_options(self):
        dictionary = {}
        for option in self.options:
            dictionary[option.option_type] = option.option_value
        return dictionary

    def bytes(self):
        # obter mensagem e criar checksum
        pim_vrs_type = (PacketPimHeader.PIM_VERSION << 4) + self.msg_type
        msg_without_chcksum = struct.pack(PacketPimHeader.PIM_HDR, pim_vrs_type, 0, 0)
        msg_without_chcksum += self.get_options_bytes()
        pim_checksum = checksum(msg_without_chcksum)
        msg = msg_without_chcksum[0:2] + struct.pack("! H", pim_checksum) + msg_without_chcksum[4:]
        return msg
