'''
Created on Jul 16, 2015

@author: alex
'''
#from des.addr import Addr

#from .messages.assert_msg import SFMRAssertMsg
#from .messages.join import SFMRJoinMsg
from .tree_interface import TreeInterface
from .upstream_prune import UpstreamState
from threading import Timer
from .globals import *
import random


class TreeInterfaceUpstream(TreeInterface):
    def __init__(self, kernel_entry, interface_id, is_originater: bool):
        TreeInterface.__init__(self, kernel_entry, interface_id)
        self._graft_prune_state = UpstreamState.Forward
        self._graft_retry_timer = None
        self._override_timer = None
        self._prune_limit_timer = None

        self._originator_state = None

        if self.is_S_directly_conn():
            self._graft_prune_state.sourceIsNowDirectConnect(self)

    ##########################################
    # Set state
    ##########################################
    def set_state(self, new_state):
        with self.get_state_lock():
            if new_state != self._graft_prune_state:
                self._graft_prune_state = new_state

                self.change_tree()
                self.evaluate_ingroup()


    ##########################################
    # Check timers
    ##########################################
    def is_graft_retry_timer_running(self):
        return self._graft_retry_timer is not None and self._graft_retry_timer.is_alive()

    def is_override_timer_running(self):
        return self._override_timer is not None and self._override_timer.is_alive()

    def is_prune_limit_timer_running(self):
        return self._prune_limit_timer is not None and self._prune_limit_timer.is_alive()

    ##########################################
    # Set timers
    ##########################################
    def set_graft_retry_timer(self, time=GRAFT_RETRY_PERIOD):
        self.clear_graft_retry_timer()
        self._graft_retry_timer = Timer(time, self.graft_retry_timeout)
        self._graft_retry_timer.start()

    def clear_graft_retry_timer(self):
        if self._graft_retry_timer is not None:
            self._graft_retry_timer.cancel()

    def set_override_timer(self):
        self.clear_override_timer()
        self._override_timer = Timer(self.t_override, self.override_timeout)
        self._override_timer.start()

    def clear_override_timer(self):
        if self._override_timer is not None:
            self._override_timer.cancel()

    def set_prune_limit_timer(self, time=T_LIMIT):
        self.clear_prune_limit_timer()
        self._prune_limit_timer = Timer(time, self.prune_limit_timeout)
        self._prune_limit_timer.start()

    def clear_prune_limit_timer(self):
        if self._prune_limit_timer is not None:
            self._prune_limit_timer.cancel()

    ###########################################
    # Timer timeout
    ###########################################
    def graft_retry_timeout(self):
        self._graft_prune_state.GRTexpires(self)

    def override_timeout(self):
        self._graft_prune_state.OTexpires(self)

    def prune_limit_timeout(self):
        return

    ###########################################
    # Recv packets
    ###########################################
    def recv_data_msg(self):
        # todo check olist
        if self.is_olist_null() and not self.is_prune_limit_timer_running() and not self.is_S_directly_conn():
            self._graft_prune_state.dataArrivesRPFinterface_OListNull_PLTstoped(self)

    def recv_state_refresh_msg(self, prune_indicator: int):
        # todo check rpf nbr
        if prune_indicator == 1:
            self._graft_prune_state.stateRefreshArrivesRPFnbr_pruneIs1(self)
        elif prune_indicator == 0 and not self.is_prune_limit_timer_running():
            self._graft_prune_state.stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(self)

    def recv_join_msg(self, upstream_neighbor_address):
        super().recv_join_msg(upstream_neighbor_address)
        # todo check rpf nbr
        self._graft_prune_state.seeJoinToRPFnbr(self)

    def recv_prune_msg(self, upstream_neighbor_address, holdtime):
        super().recv_prune_msg(upstream_neighbor_address, holdtime)
        self._graft_prune_state.seePrune(self)

    def recv_graft_ack_msg(self):
        # todo check rpf nbr
        self._graft_prune_state.recvGraftAckFromRPFnbr(self)

    ###########################################
    # Change olist
    ###########################################
    def olist_is_null(self):
        self._graft_prune_state.olistIsNowNull(self)

    def olist_is_not_null(self):
        self._graft_prune_state.olistIsNowNotNull(self)

    ###########################################
    # Changes on Unicast Routing Table
    ###########################################
    def change_rpf(self, olist_is_null):
        if olist_is_null:
            self._graft_prune_state.RPFnbrChanges_olistIsNull()
        else:
            self._graft_prune_state.RPFnbrChanges_olistIsNotNull()

    #Override
    def is_forwarding(self):
        return False

    #Override
    def delete(self):
        super().delete()

    def is_downstream(self):
        return False


    #-------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------

    @property
    def t_override(self):
        oi = self.get_interface()._override_interval
        return random.uniform(0, oi)
