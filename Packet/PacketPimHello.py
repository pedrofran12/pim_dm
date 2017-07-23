import struct

'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Option Type          |         Option Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Option Value                          |
|                              ...                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               .                               |
|                               .                               |
|                               .                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Option Type          |         Option Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Option Value                          |
|                              ...                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketPimHello:
    PIM_TYPE = 0
    PIM_HDR_OPTS = "! HH"
    PIM_HDR_OPTS_LEN = struct.calcsize(PIM_HDR_OPTS)

    PIM_MSG_TYPES_LENGTH = {1: 2,
                            20: 4,
                            }

    def __init__(self):
        self.options = {}

    def add_option(self, option_type: int, option_value: int):
        if option_value is None:
            del self.options[option_type]
            return
        self.options[option_type] = option_value

    def get_options(self):
        return self.options

    def bytes(self) -> bytes:
        res = b''
        for (option_type, option_value) in self.options.items():
            option_length = PacketPimHello.PIM_MSG_TYPES_LENGTH[option_type]
            type_length_hdr = struct.pack(PacketPimHello.PIM_HDR_OPTS, option_type, option_length)
            res += type_length_hdr + struct.pack("! " + str(option_length) + "s", option_value.to_bytes(option_length, byteorder='big'))
        return res
