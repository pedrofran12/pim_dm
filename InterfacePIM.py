import threading
import random
from Interface import Interface
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback
from RWLock.RWLock import RWLockWrite


class InterfacePim(Interface):
    MCAST_GRP = '224.0.0.13'

    def __init__(self, interface_name: str):
        super().__init__(interface_name)

        # generation id
        self.generation_id = random.getrandbits(32)

        # pim neighbors
        self.neighbors = {}
        self.neighbors_lock = RWLockWrite()

        # run receive method in background
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

    def receive(self):
        while self.is_enabled():
            try:
                packet = super().receive()
                if packet:
                    Main.protocols[packet.payload.get_pim_type()].receive_handle(packet)
            except:
                traceback.print_exc()
                continue

        """
        while self.interface_enabled:
                (raw_packet, (ip, _)) = self.socket.recvfrom(256 * 1024)
                if raw_packet:
                    packet = ReceivedPacket(raw_packet, self)
                    Main.protocols[packet.payload.get_pim_type()].receive_handle(packet)  # TODO: perceber se existe melhor maneira de fazer isto
            except Exception:
                traceback.print_exc()
                continue
        """

    def send(self, data: bytes, group_ip: str=MCAST_GRP):
        super().send(data=data, group_ip=group_ip)

    def remove(self):
        super().remove()

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
