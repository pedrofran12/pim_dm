import ipaddress
import struct
import socket
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Addr Family  | Encoding Type |B| Reserved  |Z|  Mask Len     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Group Multicast Address
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+...
'''
class PacketPimEncodedGroupAddress:
    PIM_ENCODED_GROUP_ADDRESS_HDR = "! BBBB 4s"
    PIM_ENCODED_GROUP_ADDRESS_HDR_LEN = struct.calcsize(PIM_ENCODED_GROUP_ADDRESS_HDR)

    FAMILY_RESERVED = 0
    FAMILY_IPV4 = 1
    FAMILY_IPV6 = 2

    RESERVED = 0

    def __init__(self, group_address, mask_len=32):
        if type(group_address) not in (str, bytes):
            raise Exception
        if type(group_address) is bytes:
            group_address = socket.inet_ntoa(group_address)
        self.group_address = group_address
        self.mask_len = mask_len

    def bytes(self) -> bytes:
        addr_family = self.get_addr_family(self.group_address)
        ip = socket.inet_aton(self.group_address)
        msg = struct.pack(PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR, addr_family, 0,
                          PacketPimEncodedGroupAddress.RESERVED, self.mask_len, ip)
        return msg

    def get_addr_family(self, ip):
        version = ipaddress.ip_address(ip).version
        if version == 4:
            return PacketPimEncodedGroupAddress.FAMILY_IPV4
        elif version == 6:
            return PacketPimEncodedGroupAddress.FAMILY_IPV6
        else:
            raise Exception

