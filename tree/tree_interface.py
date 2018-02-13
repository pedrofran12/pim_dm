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
from .assert_ import AssertState, AssertStateABC

from Packet.PacketPimGraft import PacketPimGraft
from Packet.PacketPimGraftAck import PacketPimGraftAck
from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup
from Packet.PacketPimHeader import PacketPimHeader
from Packet.Packet import Packet

from Packet.PacketPimJoinPrune import PacketPimJoinPrune
from Packet.PacketPimAssert import PacketPimAssert
from Packet.PacketPimStateRefresh import PacketPimStateRefresh
from .metric import AssertMetric
from threading import Timer
from .local_membership import LocalMembership
from .globals import *

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

        # Local Membership State
        try:
            interface_name = Main.kernel.vif_index_to_name_dic[interface_id]
            igmp_interface = Main.igmp_interfaces[interface_name]  # type: InterfaceIGMP
            group_state = igmp_interface.interface_state.get_group_state(kernel_entry.group_ip)
            #self._igmp_has_members = group_state.add_multicast_routing_entry(self)
            igmp_has_members = group_state.add_multicast_routing_entry(self)
            self._local_membership_state = LocalMembership.Include if igmp_has_members else LocalMembership.NoInfo
        except:
            #traceback.print_exc()
            self._local_membership_state = LocalMembership.NoInfo


        # Prune State
        self._prune_state = DownstreamState.NoInfo
        self._prune_pending_timer = None
        self._prune_timer = None

        # Assert Winner State
        self._assert_state = AssertState.NoInfo
        self._assert_winner_metric = AssertMetric()
        self._assert_timer = None

        # Received prune hold time
        self._received_prune_holdtime = None

        self._igmp_lock = RLock()

        #self.rprint('new ' + self.__class__.__name__)

    ############################################
    # Set ASSERT State
    ############################################
    def set_assert_state(self, new_state: AssertStateABC):
        with self.get_state_lock():
            if new_state != self._assert_state:
                self._assert_state = new_state

                self.change_tree()
                self.evaluate_ingroup()

    def set_assert_winner_metric(self, new_assert_metric: AssertMetric):
        import ipaddress
        with self.get_state_lock():
            try:
                old_neighbor = self.get_interface().get_neighbor(str(self._assert_winner_metric.ip_address))
                new_neighbor = self.get_interface().get_neighbor(str(new_assert_metric.ip_address))

                if old_neighbor is not None:
                    old_neighbor.unsubscribe_nlt_expiration(self)
                if new_neighbor is not None:
                    new_neighbor.subscribe_nlt_expiration(self)
                '''
                if new_assert_metric.ip_address == ipaddress.ip_address("0.0.0.0") or new_assert_metric.ip_address is None:
                    if old_neighbor is not None:
                        old_neighbor.unsubscribe_nlt_expiration(self)
                else:
                    old_neighbor.unsubscribe_nlt_expiration(self)
                    new_neighbor.subscribe_nlt_expiration(self)
                '''
            finally:
                self._assert_winner_metric = new_assert_metric


    ############################################
    # ASSERT Timer
    ############################################
    def set_assert_timer(self, time):
        self.clear_assert_timer()
        self._assert_timer = Timer(time, self.assert_timeout)
        self._assert_timer.start()

    def clear_assert_timer(self):
        if self._assert_timer is not None:
            self._assert_timer.cancel()

    def assert_timeout(self):
        self._assert_state.assertTimerExpires(self)


    ###########################################
    # Recv packets
    ###########################################
    def recv_data_msg(self):
        pass

    def recv_assert_msg(self, received_metric: AssertMetric):
        if self.my_assert_metric().is_better_than(received_metric):
            # received inferior assert
            if self._assert_winner_metric.ip_address == received_metric.ip_address:
                # received from assert winner
                self._assert_state.receivedInferiorMetricFromWinner(self)
            elif self.could_assert():
                # received from non assert winner and could_assert
                self._assert_state.receivedInferiorMetricFromNonWinner_couldAssertIsTrue(self)
        elif received_metric.is_better_than(self._assert_winner_metric):
            #received preferred assert
            self._assert_state.receivedPreferedMetric(self, received_metric)

    def recv_prune_msg(self, upstream_neighbor_address, holdtime):
        if upstream_neighbor_address == self.get_ip():
            self._assert_state.receivedPruneOrJoinOrGraft(self)

    def recv_join_msg(self, upstream_neighbor_address):
        if upstream_neighbor_address == self.get_ip():
            self._assert_state.receivedPruneOrJoinOrGraft(self)

    def recv_graft_msg(self, upstream_neighbor_address, source_ip):
        if upstream_neighbor_address == self.get_ip():
            self._assert_state.receivedPruneOrJoinOrGraft(self)

    def recv_graft_ack_msg(self, source_ip_of_graft_ack):
        return

    def recv_state_refresh_msg(self, received_metric: AssertMetric, prune_indicator):
        self.recv_assert_msg(received_metric)


    ######################################
    # Send messages
    ######################################
    def send_graft(self):
        print("send graft")
        try:
            (source, group) = self.get_tree_id()

            ip_dst = self.get_neighbor_RPF()
            ph = PacketPimGraft(ip_dst)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group,  joined_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))
            self.get_interface().send(pckt.bytes(), ip_dst)
        except:
            traceback.print_exc()
            return


    def send_graft_ack(self, ip_sender):
        print("send graft ack")
        try:
            (source, group) = self.get_tree_id()

            ph = PacketPimGraftAck(ip_sender)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group,  joined_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))
            self.get_interface().send(pckt.bytes(), ip_sender)
        except:
            traceback.print_exc()
            return


    def send_prune(self, holdtime=None):
        if holdtime is None:
            holdtime = T_LIMIT

        print("send prune")
        try:
            (source, group) = self.get_tree_id()
            ph = PacketPimJoinPrune(self.get_neighbor_RPF(), holdtime)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, pruned_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
            print('sent prune msg')
        except:
            traceback.print_exc()
            return


    def send_pruneecho(self):
        holdtime = T_LIMIT
        try:
            (source, group) = self.get_tree_id()
            ph = PacketPimJoinPrune(self.get_ip(), holdtime)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, pruned_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
            print("send prune echo")
        except:
            traceback.print_exc()
            return


    def send_join(self):
        print("send join")

        try:
            (source, group) = self.get_tree_id()
            ph = PacketPimJoinPrune(self.get_neighbor_RPF(), 210)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, joined_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
        except:
            traceback.print_exc()
            return


    def send_assert(self):
        print("send assert")

        try:
            (source, group) = self.get_tree_id()
            assert_metric = self.my_assert_metric()
            ph = PacketPimAssert(multicast_group_address=group, source_address=source, metric_preference=assert_metric.metric_preference, metric=assert_metric.route_metric)
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
        except:
            traceback.print_exc()
            return


    def send_assert_cancel(self):
        print("send assert cancel")

        try:
            (source, group) = self.get_tree_id()
            ph = PacketPimAssert(multicast_group_address=group, source_address=source, metric_preference=1, metric=float("Inf"))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
        except:
            traceback.print_exc()
            return


    def send_state_refresh(self, state_refresh_msg_received: PacketPimStateRefresh):
        pass

    #############################################################

    @abstractmethod
    def is_forwarding(self):
        pass

    def nbr_died(self):
        pass

    def nbr_connected(self):
        pass

    def assert_winner_nlt_expires(self):
        self._assert_state.winnerLivelinessTimerExpires(self)


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


    #############################################################
    # Local Membership (IGMP)
    ############################################################
    def notify_igmp(self, has_members: bool):
        with self.get_state_lock():
            with self._igmp_lock:
                if has_members != self._local_membership_state.has_members():
                    #self._igmp_has_members = has_members
                    self._local_membership_state = LocalMembership.Include if has_members else LocalMembership.NoInfo
                    self.change_tree()
                    self.evaluate_ingroup()


    def igmp_has_members(self):
        with self._igmp_lock:
        #return self._igmp_has_members
            return self._local_membership_state.has_members()

    def rprint(self, msg, *entrys):
        return

    def __str__(self):
        return '{}<{}>'.format(self.__class__, self._interface.get_link())

    def get_interface(self):
        kernel = Main.kernel
        interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        interface = Main.interfaces[interface_name]
        return interface


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




    # obtain ip of RPF'(S)
    def get_neighbor_RPF(self):
        '''
        RPF'(S)
        '''
        if self.i_am_assert_loser():
            return self._assert_winner_metric.get_ip()
        else:
            return self._kernel_entry.rpf_node

    def i_am_assert_loser(self):
        return self._assert_state == AssertState.Loser

    def is_assert_winner(self):
        return not self.is_downstream() and not self._assert_state == AssertState.Loser

    def is_S_directly_conn(self):
        return self._kernel_entry.rpf_node == self._kernel_entry.source_ip

    def set_receceived_prune_holdtime(self, holdtime):
        self._received_prune_holdtime = holdtime

    def get_received_prune_holdtime(self):
        return self._received_prune_holdtime



    ###################################################
    # ASSERT
    ###################################################
    def lost_assert(self):
        if not self.is_downstream():
            return False
        else:
            return not AssertMetric.i_am_assert_winner(self) and \
                   self._assert_winner_metric.is_better_than(AssertMetric.spt_assert_metric(self))

    def could_assert(self):
        return self.is_downstream()

    def my_assert_metric(self):
        '''
        The assert metric of this interface for usage in assert state machine
        @rtype: AssertMetric
        '''
        if self.could_assert():
            return AssertMetric.spt_assert_metric(self)
        else:
            return AssertMetric.infinite_assert_metric()
