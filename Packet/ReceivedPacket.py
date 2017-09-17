from Packet.Packet import Packet
from Packet.PacketIpHeader import PacketIpHeader
from Packet.PacketIGMPHeader import PacketIGMPHeader
from .PacketPimHeader import PacketPimHeader
from utils import TYPE_CHECKING
if TYPE_CHECKING:
    from Interface import Interface


class ReceivedPacket(Packet):
    # choose payload protocol class based on ip protocol number
    payload_protocol = {2: PacketIGMPHeader, 103: PacketPimHeader}

    def __init__(self, raw_packet: bytes, interface: 'Interface'):
        self.interface = interface
        # Parse ao packet e preencher objeto Packet

        packet_ip_hdr = raw_packet[:PacketIpHeader.IP_HDR_LEN]
        ip_header = PacketIpHeader.parse_bytes(packet_ip_hdr)
        protocol_number = ip_header.proto

        packet_without_ip_hdr = raw_packet[ip_header.hdr_length:]
        payload = ReceivedPacket.payload_protocol[protocol_number].parse_bytes(packet_without_ip_hdr)

        super().__init__(ip_header=ip_header, payload=payload)
