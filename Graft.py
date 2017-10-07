from Packet.Packet import Packet
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback

class Graft:
    TYPE = 6

    def __init__(self):
        Main.add_protocol(Graft.TYPE, self)

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        print("GRAFT!!")
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


        join_prune_groups = pkt_join_prune.groups
        for group in join_prune_groups:
            multicast_group = group.multicast_group
            joined_src_addresses = group.joined_src_addresses

            for source_address in joined_src_addresses:
                source_group = (source_address, multicast_group)
                try:
                    Main.kernel.get_routing_entry(source_group).recv_graft_msg(interface_index, packet)
                except:
                    try:
                        #import time
                        #time.sleep(2)
                        Main.kernel.get_routing_entry(source_group).recv_graft_msg(interface_index, packet)
                    except:
                        pass
                    # todo o que fazer quando n existe arvore para (s,g) ???
                    traceback.print_exc()
                    print("ATENCAO!!!!")
                    print(Main.kernel.routing)
                    continue
