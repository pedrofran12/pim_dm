from Packet.ReceivedPacket import ReceivedPacket
from utils import *
from ipaddress import IPv4Address


class IGMP:
    # receive handler
    @staticmethod
    def receive_handle(packet: ReceivedPacket):
        interface = packet.interface
        ip_src = packet.ip_header.ip_src
        ip_dst = packet.ip_header.ip_dst
        print("ip = ", ip_src)
        igmp_hdr = packet.payload

        igmp_type = igmp_hdr.type
        igmp_group = igmp_hdr.group_address

        # source ip can't be 0.0.0.0 or multicast
        if ip_src == "0.0.0.0" or IPv4Address(ip_src).is_multicast:
            return

        if igmp_type == Version_1_Membership_Report and ip_dst == igmp_group and IPv4Address(igmp_group).is_multicast:
            interface.interface_state.receive_v1_membership_report(packet)
        elif igmp_type == Version_2_Membership_Report and ip_dst == igmp_group and IPv4Address(igmp_group).is_multicast:
            interface.interface_state.receive_v2_membership_report(packet)
        elif igmp_type == Leave_Group and ip_dst == "224.0.0.2" and IPv4Address(igmp_group).is_multicast:
            interface.interface_state.receive_leave_group(packet)
        elif igmp_type == Membership_Query and (ip_dst == igmp_group or (ip_dst == "224.0.0.1" and igmp_group == "0.0.0.0")):
            interface.interface_state.receive_query(packet)
        else:
            raise Exception("Exception igmp packet: type={}; ip_dst={}; packet_group_report={}".format(igmp_type, ip_dst, igmp_group))
