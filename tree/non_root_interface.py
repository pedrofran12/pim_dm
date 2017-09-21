'''
Created on Jul 16, 2015

@author: alex
'''

#from convergence import Convergence
#from des.event.timer import Timer
from threading import Timer
from .assert_ import AssertState, SFMRAssertABC
#from .messages.assert_msg import SFMRAssertMsg
#from .messages.reset import SFMResetMsg
from .metric import SFMRAssertMetric
from .prune import SFMRPruneState, SFMRPruneStateABC
from .tree_interface import SFRMTreeInterface
from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimAssert import PacketPimAssert
from threading import Lock

class SFRMNonRootInterface(SFRMTreeInterface):
    DIPT_TIME = 3.0

    def __init__(self, kernel_entry, interface_id):
        SFRMTreeInterface.__init__(self, kernel_entry, interface_id)

        self._assert_state = AssertState.Winner
        self._assert_metric = None

        self._prune_state = SFMRPruneState.DIP
        self._dipt = None
        self.set_dipt_timer()
        self.send_prune()


    # Override
    def recv_data_msg(self, msg=None, sender=None):
        if self._prune_state != SFMRPruneState.NDI:
            self._assert_state.data_arrival(self)

    # Override
    def recv_assert_msg(self, msg: ReceivedPacket, sender=None):
        '''
        @type msg: SFMRAssertMsg
        @type sender: Addr
        '''
        if self._prune_state == SFMRPruneState.NDI:
            return

        if self._assert_state == AssertState.Looser:
            winner_metric = self._get_winner_metric()
        else:
            winner_metric = self.get_metric()

        ip_sender = msg.ip_header.ip_src
        pkt_assert = msg.payload.payload  # type: PacketPimAssert
        msg_metric = SFMRAssertMetric(metric_preference=pkt_assert.metric_preference, route_metric=pkt_assert.metric, ip_address=ip_sender)
        if winner_metric.is_worse_than(msg_metric):
            self._assert_state.recv_better_metric(self, msg_metric)
        else:
            self._assert_state.recv_worse_metric(self, msg_metric)

    # Override
    def recv_reset_msg(self, msg, sender):
        '''
        @type msg: SFMResetMsg
        @type sender: Addr
        '''
        if self._prune_state != SFMRPruneState.NDI:
            self._assert_state.recv_reset(self)

    # Override
    def recv_prune_msg(self, msg, sender, in_group):
        super().recv_prune_msg(msg, sender, in_group)
        #with self.prune_lock:
        self._prune_state.recv_prune(self)

    # Override
    def recv_join_msg(self, msg, sender, in_group):
        super().recv_join_msg(msg, sender, in_group)
        #with self.prune_lock:
        self._prune_state.recv_join(self)

    def send_assert(self):
        (source, group) = self.get_tree_id()
        from Packet.Packet import Packet
        from Packet.PacketPimHeader import PacketPimHeader
        from Packet.PacketPimAssert import PacketPimAssert
        ph = PacketPimAssert(multicast_group_address=group, source_address=source, metric_preference=10, metric=2)
        pckt = Packet(payload=PacketPimHeader(ph))
        self.get_interface().send(pckt.bytes())
        print('sent assert msg')

    def send_reset(self):
        # todo msg = SFMResetMsg(self.get_tree_id())
        msg = None

        self.get_interface().send_mcast(msg)
        self.rprint('sent reset msg')
        raise NotImplemented()

    # Override
    def send_prune(self):
        SFRMTreeInterface.send_prune(self)

    # Override
    def is_forwarding(self):
        return self._assert_state == AssertState.Winner \
            and (self.igmp_has_members() or not self.is_pruned())

    def is_pruned(self):
        return self._prune_state == SFMRPruneState.NDI

    # Override
    def nbr_died(self, node):
        # todo
        if self._get_winner_metric() is not None \
                and self._get_winner_metric().get_ip_address() == node\
                and self._prune_state != SFMRPruneState.NDI:
            self._assert_state.aw_failure(self)

        self._prune_state.lost_nbr(self)

    # Override
    def nbr_connected(self):
        self._prune_state.new_nbr(self)

    # Override
    def is_now_root(self):
        self._assert_state.is_now_root(self)
        self._prune_state.is_now_root(self)

    # Override
    def delete(self):
        SFRMTreeInterface.delete(self)
        #self._get_dipt().cancel()
        self.clear_dipt_timer()

    def __dipt_expires(self):
        print('DIPT expired')
        self._prune_state.dipt_expires(self)

    def get_metric(self):
        return SFMRAssertMetric.spt_assert_metric(self)

    def _set_assert_state(self, value: SFMRAssertABC):
        with self.get_state_lock():
            if value != self._assert_state:
                self._assert_state = value

                self.change_tree()
                self.evaluate_ingroup()
                #Convergence.mark_change()

    def _get_winner_metric(self):
        '''
        @rtype: SFMRAssertMetric
        '''
        return self._assert_metric

    def _set_winner_metric(self, value):
        assert isinstance(value, SFMRAssertMetric) or value is None
        # todo
        self._assert_metric = value

    # Override
    def set_cost(self, value):
        # todo
        """
        if value != self._cost and self._prune_state != SFMRPruneState.NDI:
            if self.is_forwarding() and value > self._cost:
                SFRMTreeInterface.set_cost(self, value)
                self._assert_state.aw_rpc_worsens(self)

            elif not self.is_forwarding(
            ) and value < self._get_winner_metric().get_metric():
                SFRMTreeInterface.set_cost(self, value)
                self._assert_state.al_rpc_better_than_aw(self)

            else:
                SFRMTreeInterface.set_cost(self, value)
        else:
            SFRMTreeInterface.set_cost(self, value)
        """
        raise NotImplemented

    def _set_prune_state(self, value: SFMRPruneStateABC):
        with self.get_state_lock():
            if value != self._prune_state:
                self._prune_state = value

                self.change_tree()
                self.evaluate_ingroup()

                if value == SFMRPruneState.NDI:
                    self._assert_state.is_now_pruned(self)


    def _get_dipt(self):
        '''
        @rtype: Timer
        '''
        return self._dipt

    def set_dipt_timer(self):
        self.clear_dipt_timer()
        timer = Timer(self.DIPT_TIME, self.__dipt_expires)
        timer.start()
        self._dipt = timer

    def clear_dipt_timer(self):
        if self._dipt is not None:
            self._dipt.cancel()
