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
    PIM_ENCODED_UNICAST_ADDRESS_HDR = "! BB 4s"
    PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN = struct.calcsize(PIM_ENCODED_UNICAST_ADDRESS_HDR)

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
        addr_family = self.get_addr_family(self.unicast_address)
        ip = socket.inet_aton(self.unicast_address)
        msg = struct.pack(PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR, addr_family, 0, ip)
        return msg

    def get_addr_family(self, ip):
        version = ipaddress.ip_address(ip).version
        if version == 4:
            return PacketPimEncodedUnicastAddress.FAMILY_IPV4
        elif version == 6:
            return PacketPimEncodedUnicastAddress.FAMILY_IPV6
        else:
            raise Exception

