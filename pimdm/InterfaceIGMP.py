import socket
import struct
from ipaddress import IPv4Address
from ctypes import create_string_buffer, addressof
import netifaces
from pimdm.Interface import Interface
from pimdm.Packet.ReceivedPacket import ReceivedPacket
from pimdm.igmp.igmp_globals import Version_1_Membership_Report, Version_2_Membership_Report, Leave_Group, Membership_Query
if not hasattr(socket, 'SO_BINDTODEVICE'):
    socket.SO_BINDTODEVICE = 25


class InterfaceIGMP(Interface):
    ETH_P_IP = 0x0800		# Internet Protocol packet
    SO_ATTACH_FILTER = 26

    FILTER_IGMP = [
        struct.pack('HBBI', 0x28, 0, 0, 0x0000000c),
        struct.pack('HBBI', 0x15, 0, 3, 0x00000800),
        struct.pack('HBBI', 0x30, 0, 0, 0x00000017),
        struct.pack('HBBI', 0x15, 0, 1, 0x00000002),
        struct.pack('HBBI', 0x6, 0, 0, 0x00040000),
        struct.pack('HBBI', 0x6, 0, 0, 0x00000000),
    ]

    def __init__(self, interface_name: str, vif_index: int):
        # SEND SOCKET
        snd_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP)

        # bind to interface
        snd_s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface_name + "\0").encode('utf-8'))

        # RECEIVE SOCKET
        rcv_s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(InterfaceIGMP.ETH_P_IP))

        # receive only IGMP packets by setting a BPF filter
        bpf_filter = b''.join(InterfaceIGMP.FILTER_IGMP)
        b = create_string_buffer(bpf_filter)
        mem_addr_of_filters = addressof(b)
        fprog = struct.pack('HL', len(InterfaceIGMP.FILTER_IGMP), mem_addr_of_filters)
        rcv_s.setsockopt(socket.SOL_SOCKET, InterfaceIGMP.SO_ATTACH_FILTER, fprog)

        # bind to interface
        rcv_s.bind((interface_name, 0x0800))
        super().__init__(interface_name=interface_name, recv_socket=rcv_s, send_socket=snd_s, vif_index=vif_index)
        self.interface_enabled = True
        from pimdm.igmp.RouterState import RouterState
        self.interface_state = RouterState(self)
        super()._enable()


    def get_ip(self):
        return netifaces.ifaddresses(self.interface_name)[netifaces.AF_INET][0]['addr']

    @property
    def ip_interface(self):
        return self.get_ip()

    def send(self, data: bytes, address: str="224.0.0.1"):
        super().send(data, address)

    def _receive(self, raw_bytes):
        if raw_bytes:
            raw_bytes = raw_bytes[14:]
            packet = ReceivedPacket(raw_bytes, self)
            ip_src = packet.ip_header.ip_src
            if not (ip_src == "0.0.0.0" or IPv4Address(ip_src).is_multicast):
                self.PKT_FUNCTIONS.get(packet.payload.get_igmp_type(), InterfaceIGMP.receive_unknown_type)(self, packet)

    ###########################################
    # Recv packets
    ###########################################
    def receive_version_1_membership_report(self, packet):
        ip_dst = packet.ip_header.ip_dst
        igmp_group = packet.payload.group_address
        if ip_dst == igmp_group and IPv4Address(igmp_group).is_multicast:
            self.interface_state.receive_v1_membership_report(packet)

    def receive_version_2_membership_report(self, packet):
        ip_dst = packet.ip_header.ip_dst
        igmp_group = packet.payload.group_address
        if ip_dst == igmp_group and IPv4Address(igmp_group).is_multicast:
            self.interface_state.receive_v2_membership_report(packet)

    def receive_leave_group(self, packet):
        ip_dst = packet.ip_header.ip_dst
        igmp_group = packet.payload.group_address
        if ip_dst == "224.0.0.2" and IPv4Address(igmp_group).is_multicast:
            self.interface_state.receive_leave_group(packet)

    def receive_membership_query(self, packet):
        ip_dst = packet.ip_header.ip_dst
        igmp_group = packet.payload.group_address
        if ip_dst == igmp_group or (ip_dst == "224.0.0.1" and igmp_group == "0.0.0.0"):
            self.interface_state.receive_query(packet)

    def receive_unknown_type(self, packet):
        return

    PKT_FUNCTIONS = {
        Version_1_Membership_Report: receive_version_1_membership_report,
        Version_2_Membership_Report: receive_version_2_membership_report,
        Leave_Group: receive_leave_group,
        Membership_Query: receive_membership_query,
    }

    ##################
    def remove(self):
        super().remove()
        self.interface_state.remove()
