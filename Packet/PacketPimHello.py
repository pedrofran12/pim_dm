import struct
from abc import ABCMeta, abstractstaticmethod
from .PacketPimHelloOptions import PacketPimHelloOptions, PacketPimHelloStateRefreshCapable, PacketPimHelloGenerationID, PacketPimHelloLANPruneDelay, PacketPimHelloHoldtime

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
                            2: 4,
                            20: 4,
                            21: 4,
                            }
    # todo: pensar melhor na implementacao state refresh capable option...

    def __init__(self):
        self.options = {}

    '''
    def add_option(self, option_type: int, option_value: int or float):
        option_value = int(option_value)
        # if option_value requires more bits than the bits available for that field: option value will have all field bits = 1
        if option_type in self.PIM_MSG_TYPES_LENGTH and self.PIM_MSG_TYPES_LENGTH[option_type] * 8 < option_value.bit_length():
            option_value = (1 << (self.PIM_MSG_TYPES_LENGTH[option_type] * 8)) - 1
        self.options[option_type] = option_value
    '''

    def add_option(self, option: 'PacketPimHelloOptions'):
        #if option_type in self.PIM_MSG_TYPES_LENGTH and self.PIM_MSG_TYPES_LENGTH[option_type] * 8 < option_value.bit_length():
        #    option_value = (1 << (self.PIM_MSG_TYPES_LENGTH[option_type] * 8)) - 1

        self.options[option.type] = option


    def get_options(self):
        return self.options

    '''
    def bytes(self) -> bytes:
        res = b''
        for (option_type, option_value) in self.options.items():
            option_length = PacketPimHello.PIM_MSG_TYPES_LENGTH[option_type]
            type_length_hdr = struct.pack(PacketPimHello.PIM_HDR_OPTS, option_type, option_length)
            res += type_length_hdr + struct.pack("! " + str(option_length) + "s", option_value.to_bytes(option_length, byteorder='big'))
        return res
    '''

    def bytes(self) -> bytes:
        res = b''
        for option in self.options.values():
            res += option.bytes()
        return res



    def __len__(self):
        return len(self.bytes())


    '''
    @staticmethod
    def parse_bytes(data: bytes):
        pim_payload = PacketPimHello()
        while data != b'':
            (option_type, option_length) = struct.unpack(PacketPimHello.PIM_HDR_OPTS,
                                                         data[:PacketPimHello.PIM_HDR_OPTS_LEN])
            print(option_type, option_length)
            data = data[PacketPimHello.PIM_HDR_OPTS_LEN:]
            print(data)
            (option_value,) = struct.unpack("! " + str(option_length) + "s", data[:option_length])
            option_value_number = int.from_bytes(option_value, byteorder='big')
            print("option value: ", option_value_number)
            
            #options_list.append({"OPTION TYPE": option_type,
            #                     "OPTION LENGTH": option_length,
            #                     "OPTION VALUE": option_value_number
            #                     })
            
            pim_payload.add_option(option_type, option_value_number)
            data = data[option_length:]

        return pim_payload
    '''

    @staticmethod
    def parse_bytes(data: bytes):
        pim_payload = PacketPimHello()
        while data != b'':
            option = PacketPimHelloOptions.parse_bytes(data)
            option_length = len(option)
            data = data[option_length:]
            pim_payload.add_option(option)
        return pim_payload
