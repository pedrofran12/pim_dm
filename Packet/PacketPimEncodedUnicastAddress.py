import ipaddress
import struct
import socket
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Addr Family  | Encoding Type |     Unicast Address
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+...
'''
class PacketPimEncodedUnicastAddress:
    PIM_ENCODED_UNICAST_ADDRESS_HDR = "! BB %s"
    PIM_ENCODED_UNICAST_ADDRESS_HDR_WITHOUT_UNICAST_ADDRESS = "! BB"

    IPV4_HDR = "4s"
    IPV6_HDR = "16s"

    # TODO ver melhor versao ip
    PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN = struct.calcsize(PIM_ENCODED_UNICAST_ADDRESS_HDR % IPV4_HDR)
    PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN_IPV6 = struct.calcsize(PIM_ENCODED_UNICAST_ADDRESS_HDR % IPV6_HDR)

    FAMILY_RESERVED = 0
    FAMILY_IPV4 = 1
    FAMILY_IPV6 = 2

    def __init__(self, unicast_address):
        if type(unicast_address) not in (str, bytes):
            raise Exception
        if type(unicast_address) is bytes:
            unicast_address = socket.inet_ntoa(unicast_address)
        self.unicast_address = unicast_address

    def bytes(self) -> bytes:
        (string_ip_hdr, hdr_addr_family, socket_family) = PacketPimEncodedUnicastAddress.get_ip_info(self.unicast_address)

        ip = socket.inet_pton(socket_family, self.unicast_address)
        msg = struct.pack(PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR % string_ip_hdr, hdr_addr_family, 0, ip)
        return msg

    @staticmethod
    def get_ip_info(ip):
        version = ipaddress.ip_address(ip).version
        if version == 4:
            return (PacketPimEncodedUnicastAddress.IPV4_HDR, PacketPimEncodedUnicastAddress.FAMILY_IPV4, socket.AF_INET)
        elif version == 6:
            return (PacketPimEncodedUnicastAddress.IPV6_HDR, PacketPimEncodedUnicastAddress.FAMILY_IPV6, socket.AF_INET6)
        else:
            raise Exception
