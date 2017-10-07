import threading
import random
from Interface import Interface
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback
from RWLock.RWLock import RWLockWrite
from Packet.PacketPimHello import PacketPimHello
from Packet.PacketPimHeader import PacketPimHeader
from Packet.Packet import Packet
from Hello import Hello
from utils import HELLO_HOLD_TIME_TIMEOUT
from threading import Timer

class InterfacePim(Interface):
    MCAST_GRP = '224.0.0.13'
    HELLO_PERIOD = 30
    PROPAGATION_DELAY = 0.5
    OVERRIDE_INTERNAL = 2.5
    MAX_TRIGGERED_HELLO_PERIOD = 5


    def __init__(self, interface_name: str):
        super().__init__(interface_name)

        # generation id
        self.generation_id = random.getrandbits(32)

        # When PIM is enabled on an interface or when a router first starts, the Hello Timer (HT)
        # MUST be set to random value between 0 and Triggered_Hello_Delay
        hello_timer_time = random.uniform(0, Hello.TRIGGERED_HELLO_DELAY)
        self.hello_timer = Timer(hello_timer_time, self.send_hello)
        self.hello_timer.start()



        # todo: state refresh capable
        self._state_refresh_capable = False

        # todo: lan delay enabled
        self._lan_delay_enabled = False

        # todo: propagation delay
        self._propagation_delay = self.PROPAGATION_DELAY

        # todo: override interval
        self._override_interval = self.OVERRIDE_INTERNAL

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

    def send_hello(self):
        self.hello_timer.cancel()

        pim_payload = PacketPimHello()
        pim_payload.add_option(1, 3.5 * Hello.TRIGGERED_HELLO_DELAY)
        pim_payload.add_option(20, self.generation_id)
        ph = PacketPimHeader(pim_payload)
        packet = Packet(payload=ph)
        self.send(packet.bytes())

        # reschedule hello_timer
        self.hello_timer = Timer(Hello.TRIGGERED_HELLO_DELAY, self.send_hello)
        self.hello_timer.start()

    def remove(self):
        self.hello_timer.cancel()
        self.hello_timer = None

        # send pim_hello timeout message
        pim_payload = PacketPimHello()
        pim_payload.add_option(1, HELLO_HOLD_TIME_TIMEOUT)
        pim_payload.add_option(20, self.generation_id)
        ph = PacketPimHeader(pim_payload)
        packet = Packet(payload=ph)
        self.send(packet.bytes())

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

    def remove_neighbor(self, ip):
        with self.neighbors_lock.genWlock():
            del self.neighbors[ip]
