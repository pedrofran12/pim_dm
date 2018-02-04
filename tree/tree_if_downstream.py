'''
Created on Jul 16, 2015

@author: alex
'''

#from convergence import Convergence
#from des.event.timer import Timer
from threading import Timer
from CustomTimer.RemainingTimer import RemainingTimer
from .assert_ import AssertState, AssertStateABC
#from .messages.assert_msg import SFMRAssertMsg
#from .messages.reset import SFMResetMsg
from .metric import AssertMetric
from .downstream_prune import DownstreamState, DownstreamStateABS
from .tree_interface import TreeInterface
from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimAssert import PacketPimAssert
from threading import Lock

class TreeInterfaceDownstream(TreeInterface):
    def __init__(self, kernel_entry, interface_id):
        TreeInterface.__init__(self, kernel_entry, interface_id)

        # State
        #self._local_membership_state = None # todo NoInfo or Include

        # Prune State
        #self._prune_state = DownstreamState.NoInfo
        #self._prune_pending_timer = None
        #self._prune_timer = None

        # Assert Winner State
        #self._assert_state = AssertState.NoInfo
        #self._assert_timer = None
        #self._assert_winner_ip = None
        #self._assert_winner_metric = None

        #self.set_dipt_timer()
        #self.send_prune()

    ##########################################
    # Set state
    ##########################################
    def set_prune_state(self, new_state: DownstreamStateABS):
        with self.get_state_lock():
            if new_state != self._prune_state:
                self._prune_state = new_state

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
        self._prune_state.PPTexpires(self, 10)

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

        #TODO if upstream_neighbor_address == self.get_ip():
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



    # Override
    def is_forwarding(self):
        return ((len(self.get_interface().neighbors) >= 1 and not self.is_pruned()) or self.igmp_has_members()) and not self.lost_assert()
        #return self._assert_state == AssertState.Winner and self.is_in_group()

    def is_pruned(self):
        return self._prune_state == DownstreamState.Pruned

    def lost_assert(self):
        return self._assert_state == AssertState.Loser

    # Override
    def nbr_connected(self):
        self._prune_state.new_nbr(self)

    # Override
    def delete(self):
        TreeInterface.delete(self)
        self.clear_assert_timer()
        self.clear_prune_timer()
        self.clear_prune_pending_timer()

    def get_metric(self):
        return AssertMetric.spt_assert_metric(self)

    def _get_winner_metric(self):
        '''
        @rtype: SFMRAssertMetric
        '''
        return self._assert_metric

    def _set_winner_metric(self, value):
        assert isinstance(value, AssertMetric) or value is None
        # todo
        self._assert_metric = value


    def is_downstream(self):
        return True

