import socket
import struct
import netifaces
import ipaddress
from socket import if_nametoindex
from ipaddress import IPv6Address
from .Interface import Interface
from .packet.ReceivedPacket import ReceivedPacket_v6
from .mld.mld_globals import MULTICAST_LISTENER_QUERY_TYPE, MULTICAST_LISTENER_DONE_TYPE, MULTICAST_LISTENER_REPORT_TYPE
from ctypes import create_string_buffer, addressof

ETH_P_IPV6 = 0x86DD  # IPv6 over bluebook
SO_ATTACH_FILTER = 26
ICMP6_FILTER = 1
IPV6_ROUTER_ALERT = 22


def ICMP6_FILTER_SETBLOCKALL():
    return struct.pack("I"*8, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)


def ICMP6_FILTER_SETPASS(type, filterp):
    return filterp[:type >> 5] + (bytes([(filterp[type >> 5] & ~(1 << ((type) & 31)))])) + filterp[(type >> 5) + 1:]


class InterfaceMLD(Interface):
    IPv6_LINK_SCOPE_ALL_NODES = IPv6Address("ff02::1")
    IPv6_LINK_SCOPE_ALL_ROUTERS = IPv6Address("ff02::2")
    IPv6_ALL_ZEROS = IPv6Address("::")

    FILTER_MLD = [
        struct.pack('HBBI', 0x28, 0, 0, 0x0000000c),
        struct.pack('HBBI', 0x15, 0, 9, 0x000086dd),
        struct.pack('HBBI', 0x30, 0, 0, 0x00000014),
        struct.pack('HBBI', 0x15, 0, 7, 0x00000000),
        struct.pack('HBBI', 0x30, 0, 0, 0x00000036),
        struct.pack('HBBI', 0x15, 0, 5, 0x0000003a),
        struct.pack('HBBI', 0x30, 0, 0, 0x0000003e),
        struct.pack('HBBI', 0x15, 2, 0, 0x00000082),
        struct.pack('HBBI', 0x15, 1, 0, 0x00000083),
        struct.pack('HBBI', 0x15, 0, 1, 0x00000084),
        struct.pack('HBBI', 0x6, 0, 0, 0x00040000),
        struct.pack('HBBI', 0x6, 0, 0, 0x00000000),
    ]

    def __init__(self, interface_name: str, vif_index: int):
        # SEND SOCKET
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)

        # set socket output interface
        if_index = if_nametoindex(interface_name)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, struct.pack('@I', if_index))

        """
        # set ICMP6 filter to only receive MLD packets
        icmp6_filter = ICMP6_FILTER_SETBLOCKALL()
        icmp6_filter = ICMP6_FILTER_SETPASS(MULTICAST_LISTENER_QUERY_TYPE, icmp6_filter)
        icmp6_filter = ICMP6_FILTER_SETPASS(MULTICAST_LISTENER_REPORT_TYPE, icmp6_filter)
        icmp6_filter = ICMP6_FILTER_SETPASS(MULTICAST_LISTENER_DONE_TYPE, icmp6_filter)
        s.setsockopt(socket.IPPROTO_ICMPV6, ICMP6_FILTER, icmp6_filter)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, True)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, False)
        s.setsockopt(socket.IPPROTO_IPV6, self.IPV6_ROUTER_ALERT, 0)
        rcv_s = s
        """

        ip_interface = "::"
        for if_addr in netifaces.ifaddresses(interface_name)[netifaces.AF_INET6]:
            ip_interface = if_addr["addr"]
            if ipaddress.IPv6Address(ip_interface.split("%")[0]).is_link_local:
                # bind to interface
                s.bind(socket.getaddrinfo(ip_interface, None, 0, socket.SOCK_RAW, 0, socket.AI_PASSIVE)[0][4])
                ip_interface = ip_interface.split("%")[0]
                break
        self.ip_interface = ip_interface

        # RECEIVE SOCKET
        rcv_s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_IPV6))

        # receive only MLD packets by setting a BPF filter
        bpf_filter = b''.join(InterfaceMLD.FILTER_MLD)
        b = create_string_buffer(bpf_filter)
        mem_addr_of_filters = addressof(b)
        fprog = struct.pack('HL', len(InterfaceMLD.FILTER_MLD), mem_addr_of_filters)
        rcv_s.setsockopt(socket.SOL_SOCKET, SO_ATTACH_FILTER, fprog)

        # bind to interface
        rcv_s.bind((interface_name, ETH_P_IPV6))

        super().__init__(interface_name=interface_name, recv_socket=rcv_s, send_socket=s, vif_index=vif_index)
        self.interface_enabled = True
        from .mld.RouterState import RouterState
        self.interface_state = RouterState(self)
        super()._enable()

    @staticmethod
    def _get_address_family():
        return socket.AF_INET6

    def get_ip(self):
        return self.ip_interface

    def send(self, data: bytes, address: str = "FF02::1"):
        # send router alert option
        cmsg_level = socket.IPPROTO_IPV6
        cmsg_type = socket.IPV6_HOPOPTS
        cmsg_data = b'\x3a\x00\x05\x02\x00\x00\x01\x00'
        self._send_socket.sendmsg([data], [(cmsg_level, cmsg_type, cmsg_data)], 0, (address, 0))

    """
    def receive(self):
        while self.interface_enabled:
            try:
                (raw_bytes, ancdata, _, src_addr) = self._recv_socket.recvmsg(256 * 1024, 500)
                if raw_bytes:
                    self._receive(raw_bytes, ancdata, src_addr)
            except Exception:
                import traceback
                traceback.print_exc()
                continue
    """

    def _receive(self, raw_bytes, ancdata, src_addr):
        if raw_bytes:
            raw_bytes = raw_bytes[14:]
            src_addr = (socket.inet_ntop(socket.AF_INET6, raw_bytes[8:24]),)
            print("MLD IP_SRC bf= ", src_addr)
            dst_addr = raw_bytes[24:40]
            (next_header,) = struct.unpack("B", raw_bytes[6:7])
            print("NEXT HEADER:", next_header)
            payload_starts_at_len = 40
            if next_header == 0:
                # Hop by Hop options
                (next_header,) = struct.unpack("B", raw_bytes[40:41])
                if next_header != 58:
                    return
                (hdr_ext_len,) = struct.unpack("B", raw_bytes[payload_starts_at_len +1:payload_starts_at_len + 2])
                if hdr_ext_len > 0:
                    payload_starts_at_len = payload_starts_at_len + 1 + hdr_ext_len*8
                else:
                    payload_starts_at_len = payload_starts_at_len + 8

            raw_bytes = raw_bytes[payload_starts_at_len:]
            ancdata = [(socket.IPPROTO_IPV6, socket.IPV6_PKTINFO, dst_addr)]
            print("RECEIVE MLD")
            print("ANCDATA: ", ancdata, "; SRC_ADDR: ", src_addr)
            packet = ReceivedPacket_v6(raw_bytes, ancdata, src_addr, 58, self)
            ip_src = packet.ip_header.ip_src
            print("MLD IP_SRC = ", ip_src)
            if not (ip_src == "::" or IPv6Address(ip_src).is_multicast):
                self.PKT_FUNCTIONS.get(packet.payload.get_mld_type(), InterfaceMLD.receive_unknown_type)(self, packet)
    """
    def _receive(self, raw_bytes, ancdata, src_addr):
        if raw_bytes:
            packet = ReceivedPacket_v6(raw_bytes, ancdata, src_addr, 58, self)
            self.PKT_FUNCTIONS[packet.payload.get_mld_type(), InterfaceMLD.receive_unknown_type](self, packet)
    """
    ###########################################
    # Recv packets
    ###########################################
    def receive_multicast_listener_report(self, packet):
        print("RECEIVE MULTICAST LISTENER REPORT")
        ip_dst = packet.ip_header.ip_dst
        mld_group = packet.payload.group_address
        ipv6_group = IPv6Address(mld_group)
        ipv6_dst = IPv6Address(ip_dst)
        if ipv6_dst == ipv6_group and ipv6_group.is_multicast:
            self.interface_state.receive_report(packet)

    def receive_multicast_listener_done(self, packet):
        print("RECEIVE MULTICAST LISTENER DONE")
        ip_dst = packet.ip_header.ip_dst
        mld_group = packet.payload.group_address
        if IPv6Address(ip_dst) == self.IPv6_LINK_SCOPE_ALL_ROUTERS and IPv6Address(mld_group).is_multicast:
            self.interface_state.receive_done(packet)

    def receive_multicast_listener_query(self, packet):
        print("RECEIVE MULTICAST LISTENER QUERY")
        ip_dst = packet.ip_header.ip_dst
        mld_group = packet.payload.group_address
        ipv6_group = IPv6Address(mld_group)
        ipv6_dst = IPv6Address(ip_dst)
        if (ipv6_group.is_multicast and ipv6_dst == ipv6_group) or\
                (ipv6_dst == self.IPv6_LINK_SCOPE_ALL_NODES and ipv6_group == self.IPv6_ALL_ZEROS):
            self.interface_state.receive_query(packet)

    def receive_unknown_type(self, packet):
        raise Exception("UNKNOWN MLD TYPE: " + str(packet.payload.get_mld_type()))

    PKT_FUNCTIONS = {
        MULTICAST_LISTENER_REPORT_TYPE: receive_multicast_listener_report,
        MULTICAST_LISTENER_DONE_TYPE: receive_multicast_listener_done,
        MULTICAST_LISTENER_QUERY_TYPE: receive_multicast_listener_query,
    }

    ##################
    def remove(self):
        super().remove()
        self.interface_state.remove()
