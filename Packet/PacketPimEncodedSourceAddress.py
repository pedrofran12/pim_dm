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
    PIM_ENCODED_SOURCE_ADDRESS_HDR = "! BBBB %s"
    PIM_ENCODED_SOURCE_ADDRESS_HDR_WITHOUT_SOURCE_ADDRESS = "! BBBB"


    IPV4_HDR = "4s"
    IPV6_HDR = "16s"

    # TODO ver melhor versao ip
    PIM_ENCODED_SOURCE_ADDRESS_HDR_LEN = struct.calcsize(PIM_ENCODED_SOURCE_ADDRESS_HDR % IPV4_HDR)
    PIM_ENCODED_SOURCE_ADDRESS_HDR_LEN_IPV6 = struct.calcsize(PIM_ENCODED_SOURCE_ADDRESS_HDR % IPV6_HDR)

    FAMILY_RESERVED = 0
    FAMILY_IPV4 = 1
    FAMILY_IPV6 = 2

    RESERVED_AND_SWR_BITS = 0

    def __init__(self, source_address, mask_len=None):
        if type(source_address) not in (str, bytes):
            raise Exception
        if type(source_address) is bytes:
            source_address = socket.inet_ntoa(source_address)
        self.source_address = source_address
        self.mask_len = mask_len

    def bytes(self) -> bytes:
        (string_ip_hdr, hdr_addr_family, socket_family) = PacketPimEncodedSourceAddress.get_ip_info(self.source_address)

        if self.mask_len is None:
            mask_len = 8 * struct.calcsize(string_ip_hdr)
        ip = socket.inet_pton(socket_family, self.source_address)

        msg = struct.pack(PacketPimEncodedSourceAddress.PIM_ENCODED_SOURCE_ADDRESS_HDR % string_ip_hdr, hdr_addr_family, 0,
                          PacketPimEncodedSourceAddress.RESERVED_AND_SWR_BITS, mask_len, ip)
        return msg

    @staticmethod
    def get_ip_info(ip):
        version = ipaddress.ip_address(ip).version
        if version == 4:
            return (PacketPimEncodedSourceAddress.IPV4_HDR, PacketPimEncodedSourceAddress.FAMILY_IPV4, socket.AF_INET)
        elif version == 6:
            return (PacketPimEncodedSourceAddress.IPV6_HDR, PacketPimEncodedSourceAddress.FAMILY_IPV6, socket.AF_INET6)
        else:
            raise Exception