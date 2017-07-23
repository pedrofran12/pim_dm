import ipaddress
import struct
import socket
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Addr Family  | Encoding Type |  Rsrvd  |S|W|R|  Mask Len     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Source Address
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+...
'''
class PacketPimEncodedSourceAddress:
    PIM_ENCODED_SOURCE_ADDRESS_HDR = "! BBBB 4s"
    PIM_ENCODED_SOURCE_ADDRESS_HDR_LEN = struct.calcsize(PIM_ENCODED_SOURCE_ADDRESS_HDR)

    FAMILY_RESERVED = 0
    FAMILY_IPV4 = 1
    FAMILY_IPV6 = 2

    RESERVED_AND_SWR_BITS = 0

    def __init__(self, source_address, mask_len=32):
        if type(source_address) not in (str, bytes):
            raise Exception
        if type(source_address) is bytes:
            source_address = socket.inet_ntoa(source_address)
        self.source_address = source_address
        self.mask_len = mask_len

    def bytes(self) -> bytes:
        addr_family = self.get_addr_family(self.source_address)
        ip = socket.inet_aton(self.source_address)
        msg = struct.pack(PacketPimEncodedSourceAddress.PIM_ENCODED_SOURCE_ADDRESS_HDR, addr_family, 0,
                          PacketPimEncodedSourceAddress.RESERVED_AND_SWR_BITS, self.mask_len, ip)
        return msg

    def get_addr_family(self, ip):
        version = ipaddress.ip_address(ip).version
        if version == 4:
            return PacketPimEncodedSourceAddress.FAMILY_IPV4
        elif version == 6:
            return PacketPimEncodedSourceAddress.FAMILY_IPV6
        else:
            raise Exception

