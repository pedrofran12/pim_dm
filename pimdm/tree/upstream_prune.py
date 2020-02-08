from abc import ABCMeta, abstractmethod
from pimdm.utils import TYPE_CHECKING
if TYPE_CHECKING:
    from .tree_if_upstream import TreeInterfaceUpstream

class UpstreamStateABC(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def dataArrivesRPFinterface_OListNull_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        Data arrives on RPF_Interface(S) AND
        olist(S, G) == NULL AND
        PLT(S, G) not running

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def RPFnbrChanges_olistIsNotNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) != NULL AND
        S not directly connected

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: Upstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: Upstream
        """
        raise NotImplementedError()


class Forward(UpstreamStateABC):
    """
    Forwarding (F)
    This is the starting state of the Upsteam(S,G) state machine.
    The state machine is in this state if it just started or if
    oiflist(S,G) != NULL.
    """

    @staticmethod
    def dataArrivesRPFinterface_OListNull_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        Data arrives on RPF_Interface(S) AND
        olist(S, G) == NULL AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug("dataArrivesRPFinterface_OListNull_PLTstoped, F -> P")

            interface.set_state(UpstreamState.Pruned)
            interface.send_prune()
            interface.set_prune_limit_timer()

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: TreeInterfaceUpstream
        """
        # if OT is not running the router must set OT to t_override seconds
        interface.join_prune_logger.debug('stateRefreshArrivesRPFnbr_pruneIs1, F -> F')
        if not interface.is_override_timer_running():
            interface.set_override_timer()

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped, F -> F')

    @staticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('seeJoinToRPFnbr, F -> F')
        interface.clear_override_timer()

    @staticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('seePrune, F -> F')
        if not interface.is_S_directly_conn() and not interface.is_override_timer_running():
            interface.set_override_timer()

    @staticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('OTexpires, F -> F')
        if not interface.is_S_directly_conn():
            interface.send_join()

    @staticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug("olistIsNowNull, F -> P")

            interface.set_state(UpstreamState.Pruned)

            interface.send_prune()
            interface.set_prune_limit_timer()

    @staticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "olistIsNowNotNull (in state F)"
        return

    @staticmethod
    def RPFnbrChanges_olistIsNotNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) != NULL AND
        S not directly connected

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug('RPFnbrChanges_olistIsNotNull, F -> AP')

            interface.set_state(UpstreamState.AckPending)

            interface.send_graft()
            interface.set_graft_retry_timer()

    @staticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('RPFnbrChanges_olistIsNull, F -> P')
        interface.set_state(UpstreamState.Pruned)

    @staticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug("sourceIsNowDirectConnect, F -> F")

    @staticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "GRTexpires (in state F)"
        return

    @staticmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug("recvGraftAckFromRPFnbr, F -> F")

    def __str__(self):
        return "Forwarding"


class Pruned(UpstreamStateABC):
    '''
    Pruned (P)
    The set, olist(S,G), is empty.
    The router will not forward data from S addressed to group G.
    '''

    @staticmethod
    def dataArrivesRPFinterface_OListNull_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        Data arrives on RPF_Interface(S) AND
        olist(S, G) == NULL AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug("dataArrivesRPFinterface_OListNull_PLTstoped, P -> P")
            interface.set_prune_limit_timer()
            interface.send_prune()

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('stateRefreshArrivesRPFnbr_pruneIs1, P -> P')
        interface.set_prune_limit_timer()

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped, P -> P')
        interface.send_prune()
        interface.set_prune_limit_timer()

    @staticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        # Do nothing
        interface.join_prune_logger.debug('seeJoinToRPFnbr, P -> P')

    @staticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('seePrune, P -> P')
        if interface.get_received_prune_holdtime() > interface.remaining_prune_limit_timer():
            interface.set_prune_limit_timer(time=interface.get_received_prune_holdtime())

    @staticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "OTexpires in state Pruned"
        return

    @staticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "olistIsNowNull in state Pruned"
        return

    @staticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug('olistIsNowNotNull, P -> AP')

            interface.clear_prune_limit_timer()

            interface.set_state(UpstreamState.AckPending)

            interface.send_graft()
            interface.set_graft_retry_timer()

    @staticmethod
    def RPFnbrChanges_olistIsNotNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) != NULL AND
        S not directly connected

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug('RPFnbrChanges_olistIsNotNull, P -> AP')

            interface.clear_prune_limit_timer()

            interface.set_state(UpstreamState.AckPending)

            interface.send_graft()
            interface.set_graft_retry_timer()

    @staticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug('RPFnbrChanges_olistIsNull, P -> P')
            interface.clear_prune_limit_timer()

    @staticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('sourceIsNowDirectConnect, P -> P')

    @staticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "GRTexpires in state Pruned"
        return

    @staticmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('recvGraftAckFromRPFnbr, P -> P')

    def __str__(self):
        return "Pruned"


class AckPending(UpstreamStateABC):
    """
    AckPending (AP)
    The router was in the Pruned(P) state, but a transition has
    occurred in the Downstream(S,G) state machine for one of this
    (S,G) entry’s outgoing interfaces, indicating that traffic from S
    addressed to G should again be forwarded. A Graft message has
    been sent to RPF’(S), but a Graft Ack message has not yet been
    received.
    """

    @staticmethod
    def dataArrivesRPFinterface_OListNull_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        Data arrives on RPF_Interface(S) AND
        olist(S, G) == NULL AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "dataArrivesRPFinterface_OListNull_PLTstoped in state AP"
        return

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('stateRefreshArrivesRPFnbr_pruneIs1, AP -> AP')
        if not interface.is_override_timer_running():
            interface.set_override_timer()

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped, AP -> F')

        interface.clear_graft_retry_timer()
        interface.set_state(UpstreamState.Forward)

    @staticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('seeJoinToRPFnbr, AP -> AP')
        interface.clear_override_timer()

    @staticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('seePrune, AP -> AP')
        if not interface.is_override_timer_running():
            interface.set_override_timer()

    @staticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('OTexpires, AP -> AP')
        interface.send_join()

    @staticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('olistIsNowNull, AP -> P')
        interface.set_state(UpstreamState.Pruned)

        interface.send_prune()

        interface.clear_graft_retry_timer()
        interface.set_prune_limit_timer()

    @staticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: TreeInterfaceUpstream
        """
        #assert False, "olistIsNowNotNull in state AP"
        return

    @staticmethod
    def RPFnbrChanges_olistIsNotNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) != NULL AND
        S not directly connected

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug('RPFnbrChanges_olistIsNotNull, AP -> AP')

            interface.send_graft()
            interface.set_graft_retry_timer()

    @staticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.join_prune_logger.debug('RPFnbrChanges_olistIsNull, AP -> P')

            interface.clear_graft_retry_timer()
            interface.set_state(UpstreamState.Pruned)

    @staticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('sourceIsNowDirectConnect, AP -> F')

        interface.set_state(UpstreamState.Forward)
        interface.clear_graft_retry_timer()

    @staticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('GRTexpires, AP -> AP')

        interface.set_graft_retry_timer()
        interface.send_graft()

    @staticmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        interface.join_prune_logger.debug('recvGraftAckFromRPFnbr, AP -> F')

        interface.clear_graft_retry_timer()
        interface.set_state(UpstreamState.Forward)

    def __str__(self):
        return "AckPending"

class UpstreamState():
    Forward = Forward()
    Pruned = Pruned()
    AckPending = AckPending()
