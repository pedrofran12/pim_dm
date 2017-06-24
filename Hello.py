import random
from threading import Timer
from Packet.Packet import Packet
from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimOption import PacketPimOption
from Packet.PacketPimHeader import PacketPimHeader
from Interface import Interface
from Main import Main
from utils import KEEP_ALIVE_PERIOD_TIMEOUT


class Hello:
    TYPE = 0
    TRIGGERED_HELLO_DELAY = 16  # TODO: configure via external file??

    def __init__(self):
        Main().add_protocol(Hello.TYPE, self)

        self.thread = Timer(Hello.TRIGGERED_HELLO_DELAY, self.send_handle)
        self.thread.start()

    def send_handle(self):
        for (ip, interface) in list(Main().interfaces.items()):
            self.packet_send_handle(interface)

        # reschedule timer
        self.thread = Timer(Hello.TRIGGERED_HELLO_DELAY, self.send_handle)
        self.thread.start()

    def packet_send_handle(self, interface: Interface):
        ph = PacketPimHeader(Hello.TYPE)
        ph.add_option(PacketPimOption(1, Hello.TRIGGERED_HELLO_DELAY))
        ph.add_option(PacketPimOption(20, interface.generation_id))
        packet = Packet(pim_header=ph)
        interface.send(packet.bytes())

    def force_send(self, interface: Interface):
        # When PIM is enabled on an interface or when a router first starts, the Hello Timer (HT)
        # MUST be set to random value between 0 and Triggered_Hello_DelayHello Timer(HT)
        hello_timer = random.uniform(0, Hello.TRIGGERED_HELLO_DELAY)
        Timer(hello_timer, self.packet_send_handle, args=[interface]).start()

    # TODO: ver melhor este metodo
    def force_send_remove(self, interface: Interface):
        ph = PacketPimHeader(Hello.TYPE)
        ph.add_option(PacketPimOption(1, KEEP_ALIVE_PERIOD_TIMEOUT))
        ph.add_option(PacketPimOption(20, interface.generation_id))
        packet = Packet(pim_header=ph)
        interface.send(packet.bytes())

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        if packet.ip_header is None:
            return  # TODO: MAYBE EXCEPCAO??

        ip = packet.ip_header.ip
        print("ip = ", ip)
        main = Main()
        options = packet.pim_header.get_options()
        if main.get_neighbor(ip) is None:
            # Unknown Neighbor
            if (1 in options) and (20 in options):
                print("non neighbor and options inside")
                main.add_neighbor(packet.interface, ip, options[20], options[1])
                return
            print("non neighbor and required options not inside")
        else:
            # Already know Neighbor
            print("neighbor conhecido")
            neighbor = main.get_neighbor(ip)
            neighbor.heartbeat()
            if 1 in options and neighbor.keep_alive_period != options[1]:
                print("keep alive period diferente")
                neighbor.set_keep_alive_period(options[1])
            if 20 in options and neighbor.generation_id != options[20]:
                print("neighbor reiniciado")
                neighbor.remove()
                main.add_neighbor(packet.interface, ip, options[20], options[1])
