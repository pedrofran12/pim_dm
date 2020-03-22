import random
from pimdm.Interface import Interface
from pimdm.Packet.ReceivedPacket import ReceivedPacket
from pimdm import Main
import traceback
from pimdm.RWLock.RWLock import RWLockWrite
from pimdm.Packet.PacketPimHelloOptions import *
from pimdm.Packet.PacketPimHello import PacketPimHello
from pimdm.Packet.PacketPimHeader import PacketPimHeader
from pimdm.Packet.Packet import Packet
from pimdm.utils import HELLO_HOLD_TIME_TIMEOUT
from threading import Timer
from pimdm.tree.globals import REFRESH_INTERVAL
import socket
import netifaces
import logging


class InterfacePim(Interface):
    MCAST_GRP = '224.0.0.13'
    PROPAGATION_DELAY = 0.5
    OVERRIDE_INTERNAL = 2.5

    HELLO_PERIOD = 30
    TRIGGERED_HELLO_PERIOD = 5

    LOGGER = logging.getLogger('pim.Interface')

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
        ip_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']
        self.ip_interface = ip_interface

        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_PIM)

        # allow other sockets to bind this port too
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # explicitly join the multicast group on the interface specified
        #s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(Interface.MCAST_GRP) + socket.inet_aton(ip_interface))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                     socket.inet_aton(Interface.MCAST_GRP) + socket.inet_aton(ip_interface))
        s.setsockopt(socket.SOL_SOCKET, 25, str(interface_name + '\0').encode('utf-8'))

        # set socket output interface
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip_interface))

        # set socket TTL to 1
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 1)

        # don't receive outgoing packets
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        super().__init__(interface_name, s, s, vif_index)
        super()._enable()
        self.force_send_hello()

    def get_ip(self):
        return self.ip_interface

    def _receive(self, raw_bytes):
        if raw_bytes:
            packet = ReceivedPacket(raw_bytes, self)
            self.PKT_FUNCTIONS[packet.payload.get_pim_type()](self, packet)

    def send(self, data: bytes, group_ip: str=MCAST_GRP):
        super().send(data=data, group_ip=group_ip)

    #Random interval for initial Hello message on bootup or triggered Hello message to a rebooting neighbor
    def force_send_hello(self):
        if self.hello_timer is not None:
            self.hello_timer.cancel()

        hello_timer_time = random.uniform(0, self.TRIGGERED_HELLO_PERIOD)
        self.hello_timer = Timer(hello_timer_time, self.send_hello)
        self.hello_timer.start()

    def send_hello(self):
        self.interface_logger.debug('Send Hello message')
        self.hello_timer.cancel()

        pim_payload = PacketPimHello()
        pim_payload.add_option(PacketPimHelloHoldtime(holdtime=3.5 * self.HELLO_PERIOD))
        pim_payload.add_option(PacketPimHelloGenerationID(self.generation_id))

        # TODO implementar LANPRUNEDELAY e OVERRIDE_INTERVAL por interface e nas maquinas de estados ler valor de interface e nao do globals.py
        #pim_payload.add_option(PacketPimHelloLANPruneDelay(lan_prune_delay=self._propagation_delay, override_interval=self._override_interval))

        if self._state_refresh_capable:
            pim_payload.add_option(PacketPimHelloStateRefreshCapable(REFRESH_INTERVAL))

        ph = PacketPimHeader(pim_payload)
        packet = Packet(payload=ph)
        self.send(packet.bytes())

        # reschedule hello_timer
        self.hello_timer = Timer(self.HELLO_PERIOD, self.send_hello)
        self.hello_timer.start()

    def remove(self):
        self.hello_timer.cancel()
        self.hello_timer = None

        # send pim_hello timeout message
        pim_payload = PacketPimHello()
        pim_payload.add_option(PacketPimHelloHoldtime(holdtime=HELLO_HOLD_TIME_TIMEOUT))
        pim_payload.add_option(PacketPimHelloGenerationID(self.generation_id))
        ph = PacketPimHeader(pim_payload)
        packet = Packet(payload=ph)
        self.send(packet.bytes())

        Main.kernel.interface_change_number_of_neighbors()
        super().remove()

    def check_number_of_neighbors(self):
        has_neighbors = len(self.neighbors) > 0
        if has_neighbors != self._had_neighbors:
            self._had_neighbors = has_neighbors
            Main.kernel.interface_change_number_of_neighbors()

    def new_or_reset_neighbor(self, neighbor_ip):
        Main.kernel.new_or_reset_neighbor(self.vif_index, neighbor_ip)

    '''
    def add_neighbor(self, ip, random_number, hello_hold_time):
        with self.neighbors_lock.genWlock():
            if ip not in self.neighbors:
                print("ADD NEIGHBOR")
                from Neighbor import Neighbor
                self.neighbors[ip] = Neighbor(self, ip, random_number, hello_hold_time)
                self.force_send_hello()
                self.check_number_of_neighbors()
    '''

    def get_neighbors(self):
        with self.neighbors_lock.genRlock():
            return self.neighbors.values()

    def get_neighbor(self, ip):
        with self.neighbors_lock.genRlock():
            return self.neighbors.get(ip)

    def remove_neighbor(self, ip):
        with self.neighbors_lock.genWlock():
            del self.neighbors[ip]
            self.interface_logger.debug("Remove neighbor: " + ip)
            self.check_number_of_neighbors()

    def set_state_refresh_capable(self, value):
        self._state_refresh_capable = value

    def is_state_refresh_enabled(self):
        return self._state_refresh_capable

    # check if Interface is StateRefreshCapable
    def is_state_refresh_capable(self):
        with self.neighbors_lock.genWlock():
            if len(self.neighbors) == 0:
                return False

            state_refresh_capable = True
            for neighbor in list(self.neighbors.values()):
                state_refresh_capable &= neighbor.state_refresh_capable

            return state_refresh_capable

    '''
    def change_interface(self):
        # check if ip change was already applied to interface
        old_ip_address = self.ip_interface
        new_ip_interface = netifaces.ifaddresses(self.interface_name)[netifaces.AF_INET][0]['addr']
        if old_ip_address == new_ip_interface:
            return
        
        self._send_socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(new_ip_interface))

        self._recv_socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
                     socket.inet_aton(Interface.MCAST_GRP) + socket.inet_aton(old_ip_address))

        self._recv_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                     socket.inet_aton(Interface.MCAST_GRP) + socket.inet_aton(new_ip_interface))

        self.ip_interface = new_ip_interface
    '''

    ###########################################
    # Recv packets
    ###########################################
    def receive_hello(self, packet):
        ip = packet.ip_header.ip_src
        print("ip = ", ip)
        options = packet.payload.payload.get_options()

        if (1 in options) and (20 in options):
            hello_hold_time = options[1].holdtime
            generation_id = options[20].generation_id
        else:
            raise Exception

        state_refresh_capable = (21 in options)


        with self.neighbors_lock.genWlock():
            if ip not in self.neighbors:
                if hello_hold_time == 0:
                    return
                print("ADD NEIGHBOR")
                from pimdm.Neighbor import Neighbor
                self.neighbors[ip] = Neighbor(self, ip, generation_id, hello_hold_time, state_refresh_capable)
                self.force_send_hello()
                self.check_number_of_neighbors()
                self.new_or_reset_neighbor(ip)
                return
            else:
                neighbor = self.neighbors[ip]

        neighbor.receive_hello(generation_id, hello_hold_time, state_refresh_capable)

    def receive_assert(self, packet):
        pkt_assert = packet.payload.payload  # type: PacketPimAssert
        source = pkt_assert.source_address
        group = pkt_assert.multicast_group_address
        source_group = (source, group)

        try:
            Main.kernel.get_routing_entry(source_group).recv_assert_msg(self.vif_index, packet)
        except:
            traceback.print_exc()

    def receive_join_prune(self, packet):
        pkt_join_prune = packet.payload.payload  # type: PacketPimJoinPrune

        join_prune_groups = pkt_join_prune.groups
        for group in join_prune_groups:
            multicast_group = group.multicast_group
            joined_src_addresses = group.joined_src_addresses
            pruned_src_addresses = group.pruned_src_addresses

            for source_address in joined_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    Main.kernel.get_routing_entry(source_group).recv_join_msg(self.vif_index, packet)
                except:
                    traceback.print_exc()
                    continue

            for source_address in pruned_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    Main.kernel.get_routing_entry(source_group).recv_prune_msg(self.vif_index, packet)
                except:
                    traceback.print_exc()
                    continue

    def receive_graft(self, packet):
        pkt_join_prune = packet.payload.payload  # type: PacketPimGraft

        join_prune_groups = pkt_join_prune.groups
        for group in join_prune_groups:
            multicast_group = group.multicast_group
            joined_src_addresses = group.joined_src_addresses

            for source_address in joined_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    Main.kernel.get_routing_entry(source_group).recv_graft_msg(self.vif_index, packet)
                except:
                    traceback.print_exc()
                    continue

    def receive_graft_ack(self, packet):
        pkt_join_prune = packet.payload.payload  # type: PacketPimGraftAck

        join_prune_groups = pkt_join_prune.groups
        for group in join_prune_groups:
            multicast_group = group.multicast_group
            joined_src_addresses = group.joined_src_addresses

            for source_address in joined_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    Main.kernel.get_routing_entry(source_group).recv_graft_ack_msg(self.vif_index, packet)
                except:
                    traceback.print_exc()
                    continue

    def receive_state_refresh(self, packet):
        if not self.is_state_refresh_enabled():
            return
        pkt_state_refresh = packet.payload.payload # type: PacketPimStateRefresh

        source = pkt_state_refresh.source_address
        group = pkt_state_refresh.multicast_group_adress
        source_group = (source, group)
        try:
            Main.kernel.get_routing_entry(source_group).recv_state_refresh_msg(self.vif_index, packet)
        except:
            traceback.print_exc()


    PKT_FUNCTIONS = {
        0: receive_hello,
        3: receive_join_prune,
        5: receive_assert,
        6: receive_graft,
        7: receive_graft_ack,
        9: receive_state_refresh,
    }
