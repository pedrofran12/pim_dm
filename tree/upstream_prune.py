from abc import ABCMeta, abstractstaticmethod
from utils import TYPE_CHECKING
if TYPE_CHECKING:
    from .tree_if_upstream import TreeInterfaceUpstream

class UpstreamStateABC(metaclass=ABCMeta):
    @abstractstaticmethod
    def dataArrivesRPFinterface_OListNull_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        Data arrives on RPF_Interface(S) AND
        olist(S, G) == NULL AND
        PLT(S, G) not running

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def RPFnbrChanges_olistIsNotNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) != NULL AND
        S not directly connected

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: Upstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
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
            interface.set_state(UpstreamState.Pruned)

            #interface.get_ot().stop()

            #timer = interface._prune_limit_timer
            #timer.set_timer(interface.t_override)
            #timer.start()
            interface.set_prune_limit_timer()

            interface.send_prune()

            print("dataArrivesRPFinterface_OListNull_PLTstoped, F -> P")

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: TreeInterfaceUpstream
        """
        #interface.set_ot()
        interface.set_override_timer()

        print('stateRefreshArrivesRPFnbr_pruneIs1, F -> F')

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """

        print(
            'stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped, F -> F')

    @staticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: TreeInterfaceUpstream
        """

        #interface.cancel_ot()
        interface.clear_override_timer()

        print('seeJoinToRPFnbr, F -> F')

    @staticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: TreeInterfaceUpstream
        """
        #interface.set_ot()
        if not interface.is_S_directly_conn():
            interface.set_override_timer()

            print('seePrune, F -> F')

    @staticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.send_join()

            print('OTexpires, F -> F')

    @staticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: TreeInterfaceUpstream
        """
        print("is direct con -> ", interface.is_S_directly_conn())
        if not interface.is_S_directly_conn():
            interface.set_state(UpstreamState.Pruned)

            #timer = interface._prune_limit_timer
            #timer.set_timer(interface.t_override)
            #timer.start()
            interface.set_prune_limit_timer()

            interface.send_prune()

            print("olistIsNowNull, F -> P")

    @staticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: TreeInterfaceUpstream
        """
        #assert False
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
            interface.send_graft()

            #interface.get_grt().start()
            interface.set_graft_retry_timer()

            interface.set_state(UpstreamState.AckPending)

            print('RPFnbrChanges_olistIsNotNull, F -> AP')

    @staticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: TreeInterfaceUpstream
        """
        interface.set_state(UpstreamState.Pruned)

        print('RPFnbrChanges_olistIsNull, F -> P')

    @staticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: TreeInterfaceUpstream
        """
        print("sourceIsNowDirectConnect, F -> F")

    @staticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        #assert False
        return

    @staticmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        print('recvGraftAckFromRPFnbr, F -> F')


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
            #interface.set_state(UpstreamState.Pruned)

            # todo send prune?!?!?!?!

            #timer = interface._prune_limit_timer
            #timer.set_timer(interface.t_override)
            #timer.start()
            interface.set_prune_limit_timer()

            print("dataArrivesRPFinterface_OListNull_PLTstoped, P -> P")

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: TreeInterfaceUpstream
        """
        #interface.get_plt().reset()
        interface.set_prune_limit_timer()

        interface.rprint('stateRefreshArrivesRPFnbr_pruneIs1, P -> P')

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """
        # todo: desnecessario pq PLT stopped????!!!
        #plt = interface.get_plt()
        #if not plt.is_ticking():
        #    plt.start()
        #    interface.send_prune()

        interface.send_prune()
        interface.set_prune_limit_timer()
        print(
            'stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped, P -> P')

    @staticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: TreeInterfaceUpstream
        """
        # Do nothing

        print('seeJoinToRPFnbr, P -> P')

    @staticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: TreeInterfaceUpstream
        """

        print('seePrune, P -> P')

    @staticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """

        #assert False
        return

    @staticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: TreeInterfaceUpstream
        """
        #assert False
        return

    @staticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.send_graft()

            #interface.get_grt().start()
            interface.set_graft_retry_timer()

            interface.set_state(UpstreamState.AckPending)

            print('olistIsNowNotNull, P -> AP')

    @staticmethod
    def RPFnbrChanges_olistIsNotNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) != NULL AND
        S not directly connected

        @type interface: TreeInterfaceUpstream
        """
        if not interface.is_S_directly_conn():
            interface.send_graft()

            #interface.get_grt().start()
            interface.set_graft_retry_timer()

            interface.set_state(UpstreamState.AckPending)

            print('olistIsNowNotNull, P -> AP')

    @staticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: TreeInterfaceUpstream
        """
        #interface.get_plt().stop()
        if not interface.is_S_directly_conn():
            interface.clear_prune_limit_timer()

            print('RPFnbrChanges_olistIsNull, P -> P')

    @staticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: TreeInterfaceUpstream
        """
        print("sourceIsNowDirectConnect, P -> P")

    @staticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        #assert False
        return

    @staticmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: TreeInterfaceUpstream
        """

        print('recvGraftAckFromRPFnbr, P -> P')

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

        #assert False
        return

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs1(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 1

        @type interface: TreeInterfaceUpstream
        """
        #interface.set_ot()
        interface.set_override_timer()

        print('stateRefreshArrivesRPFnbr_pruneIs1, AP -> AP')

    @staticmethod
    def stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped(interface: "TreeInterfaceUpstream"):
        """
        State Refresh(S,G) received from RPF‘(S) AND
        Prune Indicator == 0 AND
        PLT(S, G) not running

        @type interface: TreeInterfaceUpstream
        """

        interface.set_state(UpstreamState.Forward)
        #interface.get_grt().cancel()
        interface.clear_graft_retry_timer()

        print(
            'stateRefreshArrivesRPFnbr_pruneIs0_PLTstoped, AP -> P')

    @staticmethod
    def seeJoinToRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        See Join(S,G) to RPF’(S)

        @type interface: TreeInterfaceUpstream
        """

        #interface.cancel_ot()
        interface.clear_override_timer()

        print('seeJoinToRPFnbr, AP -> AP')

    @staticmethod
    def seePrune(interface: "TreeInterfaceUpstream"):
        """
        See Prune(S,G)

        @type interface: TreeInterfaceUpstream
        """

        #interface.set_ot()
        interface.set_override_timer()

        interface.rprint('seePrune, AP -> AP')

    @staticmethod
    def OTexpires(interface: "TreeInterfaceUpstream"):
        """
        OT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """
        interface.send_join()

        interface.rprint('OTexpires, AP -> AP')

    @staticmethod
    def olistIsNowNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->NULL

        @type interface: TreeInterfaceUpstream
        """
        interface.set_state(UpstreamState.Pruned)

        #timer = interface._prune_limit_timer
        #timer.set_timer(interface.t_override)
        interface.set_prune_limit_timer()

        #timer.start()

        #interface.get_grt().stop()
        interface.clear_graft_retry_timer()

        interface.send_prune()

        print("olistIsNowNull, AP -> P")

    @staticmethod
    def olistIsNowNotNull(interface: "TreeInterfaceUpstream"):
        """
        olist(S,G)->non-NULL

        @type interface: TreeInterfaceUpstream
        """
        #assert False
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
            interface.send_graft()

            #interface.get_grt().reset()
            interface.set_graft_retry_timer()

            print('olistIsNowNotNull, AP -> AP')

    @staticmethod
    def RPFnbrChanges_olistIsNull(interface: "TreeInterfaceUpstream"):
        """
        RPF’(S) Changes AND
        olist(S,G) == NULL

        @type interface: TreeInterfaceUpstream
        """
        #interface.get_grt().cancel()
        if not interface.is_S_directly_conn():
            interface.clear_graft_retry_timer()

            print('RPFnbrChanges_olistIsNull, AP -> P')

    @staticmethod
    def sourceIsNowDirectConnect(interface: "TreeInterfaceUpstream"):
        """
        S becomes directly connected

        @type interface: TreeInterfaceUpstream
        """
        interface.set_state(UpstreamState.Forward)
        #interface.get_grt().stop()
        interface.clear_graft_retry_timer()

        print("sourceIsNowDirectConnect, AP -> F")

    @staticmethod
    def GRTexpires(interface: "TreeInterfaceUpstream"):
        """
        GRT(S,G) Expires

        @type interface: TreeInterfaceUpstream
        """

        #interface.get_grt().start()
        interface.set_graft_retry_timer()
        interface.send_graft()

        print('GRTexpires, AP -> AP')

    @staticmethod
    def recvGraftAckFromRPFnbr(interface: "TreeInterfaceUpstream"):
        """
        Receive GraftAck(S,G) from RPF’(S)

        @type interface: TreeInterfaceUpstream
        """

        interface.set_state(UpstreamState.Forward)
        #interface.get_grt().stop()
        interface.clear_graft_retry_timer()

        print('recvGraftAckFromRPFnbr, AP -> F')

class UpstreamState():
    Forward = Forward()
    Pruned = Pruned()
    AckPending = AckPending()
