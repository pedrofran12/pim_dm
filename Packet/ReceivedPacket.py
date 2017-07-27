import struct
from Packet.Packet import Packet
from Packet.PacketIpHeader import PacketIpHeader
from Packet.PacketPimHeader import PacketPimHeader
from Packet.PacketPimHello import PacketPimHello
from Packet.PacketPimJoinPrune import PacketPimJoinPrune
from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup
import socket
from utils import checksum


class ReceivedPacket(Packet):
    def __init__(self, raw_packet, interface):
        self.interface = interface
        # Parse ao packet e preencher objeto Packet

        packet_ip_hdr = raw_packet[:PacketIpHeader.IP_HDR_LEN]
        self.ip_header = PacketIpHeader.parse_bytes(packet_ip_hdr)

        packet_without_ip_hdr = raw_packet[self.ip_header.hdr_length:]
        self.pim_header = PacketPimHeader.parse_bytes(packet_without_ip_hdr)
