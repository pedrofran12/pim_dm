import socket
from .Packet import Packet
from .PacketPimHeader import PacketPimHeader
from .PacketIpHeader import PacketIpv4Header, PacketIpv6Header
from pimdm.utils import TYPE_CHECKING
if TYPE_CHECKING:
    from pimdm.Interface import Interface


class ReceivedPacket(Packet):
    # choose payload protocol class based on ip protocol number
    payload_protocol = {103: PacketPimHeader}

    def __init__(self, raw_packet: bytes, interface: 'Interface'):
        self.interface = interface

        # Parse packet and fill Packet super class
        ip_header = PacketIpv4Header.parse_bytes(raw_packet)
        protocol_number = ip_header.proto

        packet_without_ip_hdr = raw_packet[ip_header.hdr_length:]
        payload = ReceivedPacket.payload_protocol[protocol_number].parse_bytes(packet_without_ip_hdr)

        super().__init__(ip_header=ip_header, payload=payload)


class ReceivedPacket_v6(Packet):
    # choose payload protocol class based on ip protocol number
    payload_protocol_v6 = {103: PacketPimHeader}

    def __init__(self, raw_packet: bytes, ancdata: list, src_addr: str, next_header: int, interface: 'Interface'):
        self.interface = interface

        # Parse packet and fill Packet super class
        dst_addr = "::"
        for cmsg_level, cmsg_type, cmsg_data in ancdata:
            if cmsg_level == socket.IPPROTO_IPV6 and cmsg_type == socket.IPV6_PKTINFO:
                dst_addr = socket.inet_ntop(socket.AF_INET6, cmsg_data[:16])
                break

        src_addr = src_addr[0].split("%")[0]
        ipv6_packet = PacketIpv6Header(ver=6, hop_limit=1, next_header=next_header, ip_src=src_addr, ip_dst=dst_addr)
        payload = ReceivedPacket_v6.payload_protocol_v6[next_header].parse_bytes(raw_packet)
        super().__init__(ip_header=ipv6_packet, payload=payload)
