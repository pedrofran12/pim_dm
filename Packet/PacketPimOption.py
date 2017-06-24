import struct


class PacketPimOption:
    PIM_HDR_OPTS = "! HH"
    PIM_HDR_OPTS_LEN = struct.calcsize(PIM_HDR_OPTS)

    PIM_MSG_TYPES_LENGTH = {1: 2,
                            20: 4,
                            }

    def __init__(self, option_type: int, option_value: int):
        self.option_type = option_type
        self.option_value = option_value

    def bytes(self) -> bytes:
        option_length = PacketPimOption.PIM_MSG_TYPES_LENGTH[self.option_type]
        msg = struct.pack(PacketPimOption.PIM_HDR_OPTS, self.option_type, option_length)
        return msg + struct.pack("! " + str(option_length) + "s", self.option_value.to_bytes(option_length, byteorder='big'))


