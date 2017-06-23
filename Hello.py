import random
from threading import Timer
from Packet.Packet import Packet
from Packet.PacketPimOption import PacketPimOption
from Packet.PacketPimHeader import PacketPimHeader
from Main import Main
from utils import KEEP_ALIVE_PERIOD_TIMEOUT


class Hello:
    TYPE = 0
    HELLO_HOLD_TIME = 16  # TODO: configure via external file??

    def __init__(self):
        Main().add_protocol(Hello.TYPE, self)

        self.thread = Timer(0, self.send_handle)
        self.thread.start()

    def send_handle(self):
        for (ip, interface) in Main().interfaces.items():
            self.force_send_handle(interface)

        # reschedule timer
        # Hello Timer(HT) MUST be set to random value between 0 and Triggered_Hello_Delay
        hello_timer = random.uniform(0, Hello.HELLO_HOLD_TIME)
        self.thread = Timer(hello_timer, self.send_handle)
        self.thread.start()

    def force_send_handle(self, interface):
        ph = PacketPimHeader(Hello.TYPE)
        ph.add_option(PacketPimOption(1, Hello.HELLO_HOLD_TIME))
        ph.add_option(PacketPimOption(20, interface.generation_id))
        packet = Packet(pim_header=ph)
        interface.send(packet.bytes())

    # TODO: ver melhor este metodo
    def force_send_remove_handle(self, interface):
        ph = PacketPimHeader(Hello.TYPE)
        ph.add_option(PacketPimOption(1, KEEP_ALIVE_PERIOD_TIMEOUT))
        ph.add_option(PacketPimOption(20, interface.generation_id))
        packet = Packet(pim_header=ph)
        interface.send(packet.bytes())

    # receive handler
    def receive_handle(self, packet):
        if packet.ip_header is None:
            return  # TODO: MAYBE EXCEPCAO??

        ip = packet.ip_header.ip
        print("ip = ", ip)
        # Unknown Neighbor
        main = Main()
        options = packet.pim_header.get_options()
        if main.get_neighbor(ip) is None:
            if (1 in options) and (20 in options):
                print("entrou... non neighbor and options inside")
                main.add_neighbor(packet.interface, ip, options[20], options[1])
                return
            print("entrou... non neighbor and no options inside")
        # Already know Neighbor
        else:
            print("entrou... neighbor conhecido")
            neighbor = main.get_neighbor(ip)
            neighbor.heartbeat()
            if 1 in options and neighbor.keep_alive_period != options[1]:
                print("keep alive period diferente")
                neighbor.set_keep_alive_period(options[1])
            if 20 in options and neighbor.random_number != options[20]:
                print("neighbor reiniciado")
                neighbor.remove()
                main.add_neighbor(packet.interface, ip, options[20], options[1])
