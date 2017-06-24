import socket
import threading
import random
from Packet.ReceivedPacket import ReceivedPacket

class Interface:
    #IF_IP = "10.0.0.1"
    MCAST_GRP = '224.0.0.13'

    # substituir ip por interface ou algo parecido
    def __init__(self, ip_interface: str):
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

        # run receive method in background
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

    def receive(self):
        from Main import Main
        while self.interface_enabled:
            try:
                (raw_packet, (ip, p)) = self.socket.recvfrom(256 * 1024)
                packet = ReceivedPacket(raw_packet, self)
                #print("packet received bytes: ", packet.bytes())
                #print("pim type received = ", packet.pim_header.msg_type)
                #print("generation id received = ", packet.pim_header.options[1].option_value)
                Main().protocols[packet.pim_header.msg_type].receive_handle(packet)  # TODO: perceber se existe melhor maneira de fazer isto
            except Exception:
                pass

    def send(self, data: bytes):
        if self.interface_enabled:
            self.socket.sendto(data, (Interface.MCAST_GRP, 0))

    def remove(self):
        self.interface_enabled = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        self.socket.close()
