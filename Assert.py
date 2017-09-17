from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimAssert import PacketPimAssert
import Main
import traceback


class Assert:
    TYPE = 5

    def __init__(self):
        Main.add_protocol(Assert.TYPE, self)

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        interface = packet.interface
        interface_name = interface.interface_name
        ip = packet.ip_header.ip_src
        print("ip = ", ip)
        pkt_assert = packet.payload.payload  # type: PacketPimAssert


        metric = pkt_assert.metric
        metric_preference = pkt_assert.metric_preference
        source = pkt_assert.source_address
        group = pkt_assert.multicast_group_address
        source_group = (source, group)

        interface_name = packet.interface.interface_name
        interface_index = Main.kernel.vif_name_to_index_dic[interface_name]
        try:
            #Main.kernel.routing[source_group].recv_assert_msg(interface_index, packet)
            Main.kernel.get_routing_entry(source_group).recv_assert_msg(interface_index, packet)

        except:
            traceback.print_exc()
