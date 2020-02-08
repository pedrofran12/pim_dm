'''
Created on Jul 16, 2015

@author: alex
'''
from threading import Timer
from pimdm.CustomTimer.RemainingTimer import RemainingTimer
from .assert_ import AssertState
from .downstream_prune import DownstreamState, DownstreamStateABS
from .tree_interface import TreeInterface
from pimdm.Packet.PacketPimStateRefresh import PacketPimStateRefresh
from pimdm.Packet.Packet import Packet
from pimdm.Packet.PacketPimHeader import PacketPimHeader
import traceback
import logging
from .. import Main


class TreeInterfaceDownstream(TreeInterface):
    LOGGER = logging.getLogger('pim.KernelEntry.DownstreamInterface')

    def __init__(self, kernel_entry, interface_id):
        extra_dict_logger = kernel_entry.kernel_entry_logger.extra.copy()
        extra_dict_logger['vif'] = interface_id
        extra_dict_logger['interfacename'] = Main.kernel.vif_index_to_name_dic[interface_id]
        logger = logging.LoggerAdapter(TreeInterfaceDownstream.LOGGER, extra_dict_logger)
        TreeInterface.__init__(self, kernel_entry, interface_id, logger)
        self.logger.debug('Created DownstreamInterface')
        self.join_prune_logger.debug('Downstream state transitions to ' + str(self._prune_state))

        # Last state refresh message sent (resend in case of new neighbors)
        self._last_state_refresh_message = None

    ##########################################
    # Set state
    ##########################################
    def set_prune_state(self, new_state: DownstreamStateABS):
        with self.get_state_lock():
            if new_state != self._prune_state:
                self._prune_state = new_state
                self.join_prune_logger.debug('Downstream state transitions to ' + str(new_state))

                self.change_tree()
                self.evaluate_ingroup()

    ##########################################
    # Check timers
    ##########################################
    def is_prune_pending_timer_running(self):
        return self._prune_pending_timer is not None and self._prune_pending_timer.is_alive()

    def is_prune_timer_running(self):
        return self._prune_timer is not None and self._prune_timer.is_alive()

    def remaining_prune_timer(self):
        return 0 if not self._prune_timer else self._prune_timer.time_remaining()

    ##########################################
    # Set timers
    ##########################################
    def set_prune_pending_timer(self, time):
        self.clear_prune_pending_timer()
        self._prune_pending_timer = Timer(time, self.prune_pending_timeout)
        self._prune_pending_timer.start()

    def clear_prune_pending_timer(self):
        if self._prune_pending_timer is not None:
            self._prune_pending_timer.cancel()

    def set_prune_timer(self, time):
        self.clear_prune_timer()
        #self._prune_timer = Timer(time, self.prune_timeout)
        self._prune_timer = RemainingTimer(time, self.prune_timeout)
        self._prune_timer.start()

    def clear_prune_timer(self):
        if self._prune_timer is not None:
            self._prune_timer.cancel()

    ###########################################
    # Timer timeout
    ###########################################
    def prune_pending_timeout(self):
        self._prune_state.PPTexpires(self)

    def prune_timeout(self):
        self._prune_state.PTexpires(self)

    ###########################################
    # Recv packets
    ###########################################
    def recv_data_msg(self):
        self._assert_state.receivedDataFromDownstreamIf(self)

    # Override
    def recv_prune_msg(self, upstream_neighbor_address, holdtime):
        super().recv_prune_msg(upstream_neighbor_address, holdtime)

        if upstream_neighbor_address == self.get_ip():
            self.set_receceived_prune_holdtime(holdtime)
            self._prune_state.receivedPrune(self, holdtime)

    # Override
    def recv_join_msg(self, upstream_neighbor_address):
        super().recv_join_msg(upstream_neighbor_address)

        if upstream_neighbor_address == self.get_ip():
            self._prune_state.receivedJoin(self)

    # Override
    def recv_graft_msg(self, upstream_neighbor_address, source_ip):
        print("GRAFT!!!")
        super().recv_graft_msg(upstream_neighbor_address, source_ip)

        if upstream_neighbor_address == self.get_ip():
            self._prune_state.receivedGraft(self, source_ip)


    ######################################
    # Send messages
    ######################################
    def send_state_refresh(self, state_refresh_msg_received):
        if state_refresh_msg_received is None:
            return

        self._last_state_refresh_message = state_refresh_msg_received
        if self.lost_assert() or not self.get_interface().is_state_refresh_enabled():
            return

        interval = state_refresh_msg_received.interval

        self._assert_state.sendStateRefresh(self, interval)
        self._prune_state.send_state_refresh(self)

        prune_indicator_bit = 0
        if self.is_pruned():
            prune_indicator_bit = 1

        from pimdm import UnicastRouting
        (metric_preference, metric, mask) = UnicastRouting.get_metric(state_refresh_msg_received.source_address)

        assert_override_flag = 0
        if self._assert_state == AssertState.NoInfo:
            assert_override_flag = 1

        try:
            ph = PacketPimStateRefresh(multicast_group_adress=state_refresh_msg_received.multicast_group_adress,
                                       source_address=state_refresh_msg_received.source_address,
                                       originator_adress=state_refresh_msg_received.originator_adress,
                                       metric_preference=metric_preference, metric=metric, mask_len=mask,
                                       ttl=state_refresh_msg_received.ttl - 1,
                                       prune_indicator_flag=prune_indicator_bit,
                                       prune_now_flag=state_refresh_msg_received.prune_now_flag,
                                       assert_override_flag=assert_override_flag,
                                       interval=interval)
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
        except:
            traceback.print_exc()
            return


    ##########################################################

    # Override
    def is_forwarding(self):
        return ((self.has_neighbors() and not self.is_pruned()) or self.igmp_has_members()) and not self.lost_assert()

    def is_pruned(self):
        return self._prune_state == DownstreamState.Pruned

    #def lost_assert(self):
    #    return not AssertMetric.i_am_assert_winner(self) and \
    #           self._assert_winner_metric.is_better_than(AssertMetric.spt_assert_metric(self))

    # Override
    # When new neighbor connects, send last state refresh msg
    def new_or_reset_neighbor(self, neighbor_ip):
        self.send_state_refresh(self._last_state_refresh_message)


    # Override
    def delete(self, change_type_interface=False):
        super().delete(change_type_interface)
        self.clear_assert_timer()
        self.clear_prune_timer()
        self.clear_prune_pending_timer()

    def is_downstream(self):
        return True
