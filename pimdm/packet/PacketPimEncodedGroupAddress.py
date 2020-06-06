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
    PIM_ENCODED_GROUP_ADDRESS_HDR = "! BBBB %s"
    PIM_ENCODED_GROUP_ADDRESS_HDR_WITHOUT_GROUP_MULTICAST_ADDRESS = "! BBBB"

    IPV4_HDR = "4s"
    IPV6_HDR = "16s"

    # TODO ver melhor versao ip
    PIM_ENCODED_GROUP_ADDRESS_HDR_WITHOUT_GROUP_ADDRESS_LEN = struct.calcsize(PIM_ENCODED_GROUP_ADDRESS_HDR_WITHOUT_GROUP_MULTICAST_ADDRESS)
    PIM_ENCODED_GROUP_ADDRESS_HDR_LEN = struct.calcsize(PIM_ENCODED_GROUP_ADDRESS_HDR % IPV4_HDR)
    PIM_ENCODED_GROUP_ADDRESS_HDR_LEN_IPv6 = struct.calcsize(PIM_ENCODED_GROUP_ADDRESS_HDR % IPV6_HDR)

    FAMILY_RESERVED = 0
    FAMILY_IPV4 = 1
    FAMILY_IPV6 = 2

    RESERVED = 0

    def __init__(self, group_address, mask_len=None):
        if type(group_address) not in (str, bytes):
            raise Exception
        if type(group_address) is bytes:
            group_address = socket.inet_ntoa(group_address)
        self.group_address = group_address
        self.mask_len = mask_len

    def bytes(self) -> bytes:
        (string_ip_hdr, hdr_addr_family, socket_family) = PacketPimEncodedGroupAddress.get_ip_info(self.group_address)
        mask_len = self.mask_len
        if mask_len is None:
            mask_len = 8 * struct.calcsize(string_ip_hdr)
        ip = socket.inet_pton(socket_family, self.group_address)

        msg = struct.pack(PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR % string_ip_hdr, hdr_addr_family, 0,
                          PacketPimEncodedGroupAddress.RESERVED, mask_len, ip)
        return msg

    @staticmethod
    def get_ip_info(ip):
        version = ipaddress.ip_address(ip).version
        if version == 4:
            return (PacketPimEncodedGroupAddress.IPV4_HDR, PacketPimEncodedGroupAddress.FAMILY_IPV4, socket.AF_INET)
        elif version == 6:
            return (PacketPimEncodedGroupAddress.IPV6_HDR, PacketPimEncodedGroupAddress.FAMILY_IPV6, socket.AF_INET6)
        else:
            raise Exception("Unknown address family")

    def __len__(self):
        version = ipaddress.ip_address(self.group_address).version
        if version == 4:
            return self.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN
        elif version == 6:
            return self.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN_IPv6
        else:
            raise Exception("Unknown address family")

    @staticmethod
    def parse_bytes(data: bytes):
        data_without_group_addr = data[0:PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_WITHOUT_GROUP_ADDRESS_LEN]
        (addr_family, encoding, _, mask_len) = struct.unpack(PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_WITHOUT_GROUP_MULTICAST_ADDRESS, data_without_group_addr)

        data_group_addr = data[PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_WITHOUT_GROUP_ADDRESS_LEN:]
        if addr_family == PacketPimEncodedGroupAddress.FAMILY_IPV4:
            (ip,) = struct.unpack("! " + PacketPimEncodedGroupAddress.IPV4_HDR, data_group_addr[:4])
            ip = socket.inet_ntop(socket.AF_INET, ip)
        elif addr_family == PacketPimEncodedGroupAddress.FAMILY_IPV6:
            (ip,) = struct.unpack("! " + PacketPimEncodedGroupAddress.IPV6_HDR, data_group_addr[:16])
            ip = socket.inet_ntop(socket.AF_INET6, ip)
        else:
            raise Exception("Unknown address family")

        if encoding != 0:
            print("unknown encoding")
            raise Exception

        return PacketPimEncodedGroupAddress(ip, mask_len)
