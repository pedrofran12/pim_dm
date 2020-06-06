import socket
import random
import struct
import logging
import ipaddress
import netifaces
from pimdm import Main
from socket import if_nametoindex
from pimdm.Interface import Interface
from .InterfacePIM import InterfacePim
from pimdm.rwlock.RWLock import RWLockWrite
from pimdm.packet.ReceivedPacket import ReceivedPacket_v6


class InterfacePim6(InterfacePim):
    MCAST_GRP = "ff02::d"

    def __init__(self, interface_name: str, vif_index:int, state_refresh_capable:bool=False):
        # generation id
        self.generation_id = random.getrandbits(32)

        # When PIM is enabled on an interface or when a router first starts, the Hello Timer (HT)
        # MUST be set to random value between 0 and Triggered_Hello_Delay
        self.hello_timer = None

        # state refresh capable
        self._state_refresh_capable = state_refresh_capable
        self._neighbors_state_refresh_capable = False

        # todo: lan delay enabled
        self._lan_delay_enabled = False

        # todo: propagation delay
        self._propagation_delay = self.PROPAGATION_DELAY

        # todo: override interval
        self._override_interval = self.OVERRIDE_INTERNAL

        # pim neighbors
        self._had_neighbors = False
        self.neighbors = {}
        self.neighbors_lock = RWLockWrite()
        self.interface_logger = logging.LoggerAdapter(InterfacePim.LOGGER, {'vif': vif_index, 'interfacename': interface_name})

        # SOCKET
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_PIM)

        ip_interface = ""
        for if_addr in netifaces.ifaddresses(interface_name)[netifaces.AF_INET6]:
            ip_interface = if_addr["addr"]
            if ipaddress.IPv6Address(if_addr['addr'].split("%")[0]).is_link_local:
                ip_interface = if_addr['addr'].split("%")[0]
                # bind to interface
                s.bind(socket.getaddrinfo(if_addr['addr'], None, 0, socket.SOCK_RAW, 0, socket.AI_PASSIVE)[0][4])
                break

        self.ip_interface = ip_interface

        # allow other sockets to bind this port too
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # explicitly join the multicast group on the interface specified
        if_index = if_nametoindex(interface_name)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP,
                     socket.inet_pton(socket.AF_INET6, InterfacePim6.MCAST_GRP) + struct.pack('@I', if_index))
        s.setsockopt(socket.SOL_SOCKET, 25, str(interface_name + '\0').encode('utf-8'))

        # set socket output interface
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, struct.pack('@I', if_index))

        # set socket TTL to 1
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, 1)

        # don't receive outgoing packets
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0)
        Interface.__init__(self, interface_name, s, s, vif_index)
        Interface._enable(self)
        self.force_send_hello()

    @staticmethod
    def get_kernel():
        return Main.kernel_v6

    def send(self, data: bytes, group_ip: str=MCAST_GRP):
        super().send(data=data, group_ip=group_ip)

    def _receive(self, raw_bytes, ancdata, src_addr):
        if raw_bytes:
            packet = ReceivedPacket_v6(raw_bytes, ancdata, src_addr, 103, self)
            self.PKT_FUNCTIONS[packet.payload.get_pim_type()](self, packet)
