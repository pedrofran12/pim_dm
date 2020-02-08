'''
Created on Jul 16, 2015

@author: alex
'''
from abc import ABCMeta, abstractmethod
from .. import Main
from threading import RLock
import traceback

from .downstream_prune import DownstreamState
from .assert_ import AssertState, AssertStateABC

from pimdm.Packet.PacketPimGraft import PacketPimGraft
from pimdm.Packet.PacketPimGraftAck import PacketPimGraftAck
from pimdm.Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup
from pimdm.Packet.PacketPimHeader import PacketPimHeader
from pimdm.Packet.Packet import Packet

from pimdm.Packet.PacketPimJoinPrune import PacketPimJoinPrune
from pimdm.Packet.PacketPimAssert import PacketPimAssert
from pimdm.Packet.PacketPimStateRefresh import PacketPimStateRefresh
from .metric import AssertMetric
from threading import Timer
from .local_membership import LocalMembership
from .globals import *
import logging

class TreeInterface(metaclass=ABCMeta):
    def __init__(self, kernel_entry, interface_id, logger: logging.LoggerAdapter):
        self._kernel_entry = kernel_entry
        self._interface_id = interface_id
        self.logger = logger
        self.assert_logger = logging.LoggerAdapter(logger.logger.getChild('Assert'), logger.extra)
        self.join_prune_logger = logging.LoggerAdapter(logger.logger.getChild('JoinPrune'), logger.extra)

        # Local Membership State
        try:
            interface_name = Main.kernel.vif_index_to_name_dic[interface_id]
            igmp_interface = Main.igmp_interfaces[interface_name]  # type: InterfaceIGMP
            group_state = igmp_interface.interface_state.get_group_state(kernel_entry.group_ip)
            #self._igmp_has_members = group_state.add_multicast_routing_entry(self)
            igmp_has_members = group_state.add_multicast_routing_entry(self)
            self._local_membership_state = LocalMembership.Include if igmp_has_members else LocalMembership.NoInfo
        except:
            self._local_membership_state = LocalMembership.NoInfo


        # Prune State
        self._prune_state = DownstreamState.NoInfo
        self._prune_pending_timer = None
        self._prune_timer = None

        # Assert Winner State
        self._assert_state = AssertState.NoInfo
        self._assert_winner_metric = AssertMetric()
        self._assert_timer = None
        self.assert_logger.debug("Assert state transitions to NoInfo")

        # Received prune hold time
        self._received_prune_holdtime = None

        self._igmp_lock = RLock()


    ############################################
    # Set ASSERT State
    ############################################
    def set_assert_state(self, new_state: AssertStateABC):
        with self.get_state_lock():
            if new_state != self._assert_state:
                self._assert_state = new_state
                self.assert_logger.debug('Assert state transitions to ' + str(new_state))

                self.change_tree()
                self.evaluate_ingroup()

    def set_assert_winner_metric(self, new_assert_metric: AssertMetric):
        with self.get_state_lock():
            try:
                old_neighbor = self.get_interface().get_neighbor(self._assert_winner_metric.get_ip())
                new_neighbor = self.get_interface().get_neighbor(new_assert_metric.get_ip())

                if old_neighbor is not None:
                    old_neighbor.unsubscribe_nlt_expiration(self)
                if new_neighbor is not None:
                    new_neighbor.subscribe_nlt_expiration(self)
            except:
                traceback.print_exc()
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
        if self._assert_winner_metric.is_better_than(received_metric) and \
                self._assert_winner_metric.ip_address == received_metric.ip_address:
            # received inferior assert from Assert Winner
            self._assert_state.receivedInferiorMetricFromWinner(self)
        elif self.my_assert_metric().is_better_than(received_metric) and self.could_assert():
            # received inferior assert from non assert winner and could_assert
            self._assert_state.receivedInferiorMetricFromNonWinner_couldAssertIsTrue(self)
        elif received_metric.is_better_than(self._assert_winner_metric) or \
                received_metric.equal_metric(self._assert_winner_metric):
            #received preferred assert
            equal_metric = received_metric.equal_metric(self._assert_winner_metric)
            self._assert_state.receivedPreferedMetric(self, received_metric, equal_metric)

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
            ph = PacketPimAssert(multicast_group_address=group, source_address=source, metric_preference=float("Inf"), metric=float("Inf"))
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

    def assert_winner_nlt_expires(self):
        self._assert_state.winnerLivelinessTimerExpires(self)

    @abstractmethod
    def new_or_reset_neighbor(self, neighbor_ip):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, change_type_interface=False):
        if change_type_interface:
            if self.could_assert():
                self._assert_state.couldAssertIsNowFalse(self)
            else:
                self._assert_state.couldAssertIsNowTrue(self)

        (s, g) = self.get_tree_id()
        # unsubscribe igmp information
        try:
            interface_name = Main.kernel.vif_index_to_name_dic[self._interface_id]
            igmp_interface = Main.igmp_interfaces[interface_name]  # type: InterfaceIGMP
            group_state = igmp_interface.interface_state.get_group_state(g)
            group_state.remove_multicast_routing_entry(self)
        except:
            pass

        # Prune State
        self._prune_state = None

        # Assert State
        self._assert_state = None
        self.set_assert_winner_metric(AssertMetric.infinite_assert_metric()) # unsubscribe from current AssertWinner NeighborLivenessTimer
        self._assert_winner_metric = None
        self.clear_assert_timer()

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
                    self._local_membership_state = LocalMembership.Include if has_members else LocalMembership.NoInfo
                    self.change_tree()
                    self.evaluate_ingroup()


    def igmp_has_members(self):
        with self._igmp_lock:
            return self._local_membership_state.has_members()

    def get_interface(self):
        kernel = Main.kernel
        interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        interface = Main.interfaces[interface_name]
        return interface


    def get_ip(self):
        ip = self.get_interface().get_ip()
        return ip

    def has_neighbors(self):
        try:
            return len(self.get_interface().neighbors) > 0
        except:
            return False

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
            return not self._assert_winner_metric.i_am_assert_winner(self) and \
                   self._assert_winner_metric.is_better_than(AssertMetric.spt_assert_metric(self))

    def i_am_assert_loser(self):
        return self._assert_state == AssertState.Loser

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
