from Packet.Packet import Packet
from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimJoinPrune import PacketPimJoinPrune
from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup
from Interface import Interface
import Main
import traceback

class JoinPrune:
    TYPE = 3

    def __init__(self):
        Main.add_protocol(JoinPrune.TYPE, self)

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        interface = packet.interface
        ip = packet.ip_header.ip_src
        print("ip = ", ip)
        pkt_join_prune = packet.payload.payload  # type: PacketPimJoinPrune


        # if im not upstream neighbor ignore message
        if pkt_join_prune.upstream_neighbor_address != interface.ip_interface:
            #return
            pass

        interface_name = interface.interface_name
        interface_index = Main.kernel.vif_name_to_index_dic[interface_name]


        # todo holdtime
        holdtime = pkt_join_prune.hold_time
        join_prune_groups = pkt_join_prune.groups
        for group in join_prune_groups:
            multicast_group = group.multicast_group
            joined_src_addresses = group.joined_src_addresses
            pruned_src_addresses = group.pruned_src_addresses

            for source_address in joined_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    #Main.kernel.routing[source_group].recv_join_msg(interface_index, packet)
                    Main.kernel.get_routing_entry(source_group).recv_join_msg(interface_index, packet)
                except:
                    # todo o que fazer quando n existe arvore para (s,g) ???
                    traceback.print_exc()
                    print("ATENCAO!!!!")
                    print(Main.kernel.routing)
                    continue

            for source_address in pruned_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    #Main.kernel.routing[source_group].recv_prune_msg(interface_index, packet)
                    Main.kernel.get_routing_entry(source_group).recv_prune_msg(interface_index, packet)
                except:
                    # todo o que fazer quando n existe arvore para (s,g) ???
                    traceback.print_exc()
                    print("ATENCAO!!!!")
                    print(Main.kernel.routing)
                    continue
