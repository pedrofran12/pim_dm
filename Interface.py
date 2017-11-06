import socket
import threading
import random
import netifaces
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback
from RWLock.RWLock import RWLockWrite


class Interface(object):
    MCAST_GRP = '224.0.0.13'

    # substituir ip por interface ou algo parecido
    def __init__(self, interface_name: str):
        self.interface_name = interface_name
        ip_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']
        self.ip_mask_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['netmask']
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

        # don't receive outgoing packets
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        self.socket = s
        self.interface_enabled = True

        # generation id
        #self.generation_id = random.getrandbits(32)

        # todo neighbors
        #self.neighbors = {}
        #self.neighbors_lock = RWLockWrite()

        # run receive method in background
        #receive_thread = threading.Thread(target=self.receive)
        #receive_thread.daemon = True
        #receive_thread.start()

    def receive(self):
        try:
            (raw_packet, (ip, _)) = self.socket.recvfrom(256 * 1024)
            if raw_packet:
                packet = ReceivedPacket(raw_packet, self)
            else:
                packet = None
            return packet
        except Exception:
            return None

    """
    while self.interface_enabled:
        try:
            (raw_packet, (ip, _)) = self.socket.recvfrom(256 * 1024)
            if raw_packet:
                packet = ReceivedPacket(raw_packet, self)
                Main.protocols[packet.payload.get_pim_type()].receive_handle(packet)  # TODO: perceber se existe melhor maneira de fazer isto
        except Exception:
            traceback.print_exc()
            continue
    """

    def send(self, data: bytes, group_ip: str):
        if self.interface_enabled and data:
            self.socket.sendto(data, (group_ip, 0))

    def remove(self):
        self.interface_enabled = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        self.socket.close()

    def is_enabled(self):
        return self.interface_enabled

    def get_ip(self):
        return self.ip_interface

    """
    def add_neighbor(self, ip, random_number, hello_hold_time):
        with self.neighbors_lock.genWlock():
            if ip not in self.neighbors:
                print("ADD NEIGHBOR")
                from Neighbor import Neighbor
                n = Neighbor(self, ip, random_number, hello_hold_time)
                self.neighbors[ip] = n
                Main.protocols[0].force_send(self)


    def get_neighbors(self):
        with self.neighbors_lock.genRlock():
            return self.neighbors.values()

    def get_neighbor(self, ip):
        with self.neighbors_lock.genRlock():
            return self.neighbors[ip]
    """