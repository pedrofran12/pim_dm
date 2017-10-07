'''
Created on Jul 16, 2015

@author: alex
'''
from abc import ABCMeta, abstractmethod
import Main
from threading import Lock, RLock
import traceback

#from convergence import Convergence
#from sfmr.messages.prune import SFMRPruneMsg
#from .router_interface import SFMRInterface
from .downstream_prune import DownstreamState
from .assert_ import AssertState

from Packet.PacketPimGraft import PacketPimGraft
from Packet.PacketPimGraftAck import PacketPimGraftAck
from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup
from Packet.PacketPimHeader import PacketPimHeader
from Packet.Packet import Packet

from Packet.PacketPimJoinPrune import PacketPimJoinPrune
from Packet.PacketPimAssert import PacketPimAssert
from Packet.PacketPimStateRefresh import PacketPimStateRefresh

class TreeInterface(metaclass=ABCMeta):
    def __init__(self, kernel_entry, interface_id):
        '''
        @type interface: SFMRInterface
        @type node: Node
        '''
        #assert isinstance(interface, SFMRInterface)

        self._kernel_entry = kernel_entry
        self._interface_id = interface_id
        #self._interface = interface
        #self._node = node
        #self._tree_id = tree_id
        #self._cost = cost
        #self._evaluate_ig = evaluate_ig_cb

        try:
            interface_name = Main.kernel.vif_index_to_name_dic[interface_id]
            igmp_interface = Main.igmp_interfaces[interface_name]  # type: InterfaceIGMP
            group_state = igmp_interface.interface_state.get_group_state(kernel_entry.group_ip)
            self._igmp_has_members = group_state.add_multicast_routing_entry(self)
        except:
            #traceback.print_exc()
            self._igmp_has_members = False


        # Local Membership State
        self._local_membership_state = None # todo NoInfo or Include

        # Prune State
        self._prune_state = DownstreamState.NoInfo
        self._prune_pending_timer = None
        self._prune_timer = None

        # Assert Winner State
        self._assert_state = AssertState.Winner
        self._assert_timer = None
        self._assert_winner_ip = None
        self._assert_winner_metric = None




        self._igmp_lock = RLock()

        #self.rprint('new ' + self.__class__.__name__)

    def recv_data_msg(self):
        pass

    def recv_assert_msg(self):
        pass

    def recv_reset_msg(self):
        pass

    def recv_prune_msg(self):
        pass

    def recv_join_msg(self):
        pass

    def recv_graft_msg(self):
        pass

    def recv_graft_ack_msg(self):
        pass

    def recv_state_refresh_msg(self, prune_indicator):
        pass




    def forward_state_reset_msg(self):
        raise NotImplemented


    ######################################
    # Send messages
    ######################################
    def send_graft(self):
        print("send graft")
        try:
            (source, group) = self.get_tree_id()

            # todo self.get_rpf_()
            ph = PacketPimGraft("10.0.0.13")
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group,  joined_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))
            self.get_interface().send(pckt.bytes())

            #msg = GraftMsg(self.get_tree().tree_id, self.get_rpf_())
            #self.pim_if.send_mcast(msg)
        except:
            return

    def send_graft_ack(self):
        print("send graft ack")
        try:
            (source, group) = self.get_tree_id()

            # todo endereco?!!
            ph = PacketPimGraftAck("10.0.0.13")
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group,  joined_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))
            self.get_interface().send(pckt.bytes())

            #msg = GraftAckMsg(self.get_tree().tree_id, self.get_node())
            #self.pim_if.send_mcast(msg)
        except:
            return



    def send_prune(self):
        print("send prune")
        try:
            (source, group) = self.get_tree_id()
            # todo help ip of ph
            ph = PacketPimJoinPrune("123.123.123.123", 210)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, pruned_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
            print('sent prune msg')
        except:
            return


    def send_pruneecho(self):
        print("send prune echo")

        # todo
        #msg = PruneMsg(self.get_tree().tree_id,
        #               self.get_node(), self._assert_timer.time_left())
        #self.pim_if.send_mcast(msg)
        return

    def send_join(self):
        print("send join")

        try:
            (source, group) = self.get_tree_id()
            # todo help ip of ph
            ph = PacketPimJoinPrune("123.123.123.123", 210)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, joined_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
            #msg = JoinMsg(self.get_tree().tree_id, self.get_rpf_())
            #self.pim_if.send_mcast(msg)
        except:
            return


    def send_assert(self):
        print("send assert")

        import UnicastRouting
        try:
            (source, group) = self.get_tree_id()
            (entry_protocol, entry_cost) = UnicastRouting.get_metric(source)
            # todo help ip of ph
            ph = PacketPimAssert(multicast_group_address=group, source_address=source, metric_preference=entry_protocol, metric=entry_cost)
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
            #msg = AssertMsg(self.tree_id, self.assert_metric)
            #self.pim_if.send_mcast(msg)
        except:
            return




    def send_assert_cancel(self):
        print("send cancel")

        #msg = AssertMsg.new_assert_cancel(self.tree_id)
        #self.pim_if.send_mcast(msg)
        pass

    @abstractmethod
    def is_forwarding(self):
        pass

    def nbr_died(self, node):
        pass

    def nbr_connected(self):
        pass

    #@abstractmethod
    def is_now_root(self):
        pass

    @abstractmethod
    def delete(self):
        print('Tree Interface deleted')

    def is_olist_null(self):
        return self._kernel_entry.is_olist_null()

    def evaluate_ingroup(self):
        self._kernel_entry.evaluate_olist_change()

    def notify_igmp(self, has_members: bool):
        with self.get_state_lock():
            #with self._igmp_lock:
            if has_members != self._igmp_has_members:
                self._igmp_has_members = has_members
                self.change_tree()
                self.evaluate_ingroup()


    def igmp_has_members(self):
        #with self._igmp_lock:
        return self._igmp_has_members

    def rprint(self, msg, *entrys):
        return

    def __str__(self):
        return '{}<{}>'.format(self.__class__, self._interface.get_link())

    def get_link(self):
        # todo
        return self._interface.get_link()

    def get_interface(self):
        kernel = Main.kernel
        interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        interface = Main.interfaces[interface_name]
        return interface

    def get_node(self):
        # todo: para ser substituido por get_ip
        return self.get_ip()

    def get_ip(self):
        ip = self.get_interface().get_ip()
        return ip

    def get_tree_id(self):
        return (self._kernel_entry.source_ip, self._kernel_entry.group_ip)

    def change_tree(self):
        self._kernel_entry.change()

    def get_state_lock(self):
        return self._kernel_entry.CHANGE_STATE_LOCK

    @abstractmethod
    def is_downstream(self):
        raise NotImplementedError()


    def get_rpf_(self):
        return self.get_neighbor_RPF()


    # obtain ip of RPF'(S)
    def get_neighbor_RPF(self):
        '''
        RPF'(S)
        '''
        if not self.is_assert_winner():
            return self._assert_winner_ip
        else:
            return self._kernel_entry._rpf_node

    def is_assert_winner(self):
        return not self.is_downstream() and not self._assert_state == AssertState.Loser