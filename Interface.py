import socket
import threading
import random
import netifaces
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback

class Interface(object):
    MCAST_GRP = '224.0.0.13'

    # substituir ip por interface ou algo parecido
    def __init__(self, interface_name: str):
        self.interface_name = interface_name
        ip_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']
        self.ip_interface = ip_interface

        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_PIM)

        # allow other sockets to bind this port too
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # explicitly join the multicast group on the interface specified
        s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(Interface.MCAST_GRP) + socket.inet_aton(ip_interface))

        # set socket output interface
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip_interface))

        # set socket TTL to 1
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)

        # don't receive outgoing packets
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        self.socket = s
        self.interface_enabled = True

        # generation id
        self.generation_id = random.getrandbits(32)

        # todo neighbors
        self.neighbors = {}

        # run receive method in background
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

    def receive(self):
        while self.interface_enabled:
            try:
                (raw_packet, (ip, _)) = self.socket.recvfrom(256 * 1024)
                if raw_packet:
                    packet = ReceivedPacket(raw_packet, self)
                    Main.protocols[packet.payload.get_pim_type()].receive_handle(packet)  # TODO: perceber se existe melhor maneira de fazer isto
            except Exception:
                traceback.print_exc()
                continue

    def send(self, data: bytes):
        if self.interface_enabled and data:
            self.socket.sendto(data, (Interface.MCAST_GRP, 0))

    def remove(self):
        self.interface_enabled = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        self.socket.close()
