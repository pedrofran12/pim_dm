import random
from threading import Timer
from Packet.Packet import Packet
from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimHello import PacketPimHello
from Packet.PacketPimHeader import PacketPimHeader
from Packet.PacketPimStateRefresh import PacketPimStateRefresh
from Interface import Interface
import Main


class StateRefresh:
    TYPE = 9

    def __init__(self):
        Main.add_protocol(StateRefresh.TYPE, self)

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        #check if interface supports state refresh
        if not packet.interface._state_refresh_capable:
            return
        ip = packet.ip_header.ip_src
        print("ip = ", ip)
        pkt_state_refresh = packet.payload.payload # type: PacketPimStateRefresh
        # TODO

        interface_index = packet.interface.vif_index
        source = pkt_state_refresh.source_address
        group = pkt_state_refresh.multicast_group_adress
        source_group = (source, group)


        try:
            Main.kernel.get_routing_entry(source_group).recv_state_refresh_msg(interface_index, packet)
        except:
            try:
                # import time
                # time.sleep(2)
                Main.kernel.get_routing_entry(source_group).recv_state_refresh_msg(interface_index, packet)
            except:
                pass

