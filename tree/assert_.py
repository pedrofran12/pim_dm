from abc import ABCMeta, abstractstaticmethod

import tree.globals as pim_globals
from .metric import AssertMetric
from utils import TYPE_CHECKING
if TYPE_CHECKING:
    from .tree_if_downstream import TreeInterfaceDownstream


class AssertStateABC(metaclass=ABCMeta):
    @abstractstaticmethod
    def receivedDataFromDownstreamIf(interface: "TreeInterfaceDownstream"):
        """
        An (S,G) Data packet received on downstream interface

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        """
        Receive Inferior (Assert OR State Refresh) from Assert Winner

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        """
        Receive Inferior (Assert OR  State Refresh) from non-Assert Winner
        AND CouldAssert==TRUE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedPreferedMetric(interface: "TreeInterfaceDownstream", better_metric):
        """
        Receive Preferred Assert OR State Refresh

        @type interface: TreeInterface
        @type better_metric: AssertMetric
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", time):
        """
        Send State Refresh


        @type interface: TreeInterface
        @type time: int
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        """
        AT(S,G) Expires

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        """
        CouldAssert -> FALSE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        """
        CouldAssert -> TRUE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        """
        Winner’s NLT(N,I) Expires

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        """
        Receive Prune(S,G), Join(S,G) or Graft(S,G)

        @type interface: TreeInterface
        """
        raise NotImplementedError()


    def _sendAssert_setAT(interface: "TreeInterfaceDownstream"):
        #interface.assert_timer.set_timer(pim_globals.ASSERT_TIME)
        interface.set_assert_timer(pim_globals.ASSERT_TIME)
        interface.send_assert()
        #interface.assert_timer.reset()

    @staticmethod
    def rprint(interface: "TreeInterfaceDownstream", msg, *entrys):
        '''
        Method used for simplifiyng the process of reporting changes in a assert state
        Tree Interface.
        @type interface: TreeInterface
        '''
        print(msg, 'assert state', *entrys)

    # Override
    def __str__(self) -> str:
        return "PruneSM:" + self.__class__.__name__


class NoInfoState(AssertStateABC):
    '''
    NoInfoState (NI)
    This router has no (S,G) Assert state on interface I.
    '''

    @staticmethod
    def receivedDataFromDownstreamIf(interface: "TreeInterfaceDownstream"):
        """
        @type interface: TreeInterface
        """
        interface.set_assert_state(AssertState.Winner)
        interface.set_assert_winner_metric(interface.my_assert_metric())

        NoInfoState._sendAssert_setAT(interface)
        #interface.assert_winner_metric = interface.assert_metric

        print('receivedDataFromDownstreamIf, NI -> W')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        interface.set_assert_state(AssertState.Winner)
        interface.set_assert_winner_metric(interface.my_assert_metric())

        NoInfoState._sendAssert_setAT(interface)
        #interface.assert_state = AssertState.Winner
        #interface.assert_winner_metric = interface.assert_metric

        print(
            'receivedInferiorMetricFromNonWinner_couldAssertIsTrue, NI -> W')

    @staticmethod
    def receivedPreferedMetric(interface: "TreeInterfaceDownstream", better_metric):
        '''
        @type interface: TreeInterface
        '''
        state_refresh_interval = better_metric.state_refresh_interval
        if state_refresh_interval is None:
            # event caused by Assert Msg
            assert_timer_value = pim_globals.ASSERT_TIME
        else:
            # event caused by StateRefreshMsg
            assert_timer_value = state_refresh_interval*3

        interface.set_assert_timer(assert_timer_value)
        interface.set_assert_winner_metric(better_metric)
        interface.set_assert_state(AssertState.Loser)

        # MUST also multicast a Prune(S,G) to the Assert winner
        if interface.could_assert():
            interface.send_prune(holdtime=assert_timer_value)

        print('receivedPreferedMetric, NI -> L')

    @staticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", time):
        pass

    @staticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        print('couldAssertIsNowFalse, NI -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        print('couldAssertIsNowTrue, NI -> NI')

    @staticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        print('receivedPruneOrJoinOrGraft, NI -> NI')


class WinnerState(AssertStateABC):
    '''
    I am Assert Winner (W)
    This router has won an (S,G) Assert on interface I. It is now
    responsible for forwarding traffic from S destined for G via
    interface I.
    '''

    @staticmethod
    def receivedDataFromDownstreamIf(interface: "TreeInterfaceDownstream"):
        """
        @type interface: TreeInterface
        """
        WinnerState._sendAssert_setAT(interface)

        print('receivedDataFromDownstreamIf, W -> W')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        WinnerState._sendAssert_setAT(interface)

        print(
            'receivedInferiorMetricFromNonWinner_couldAssertIsTrue, W -> W')

    @staticmethod
    def receivedPreferedMetric(interface: "TreeInterfaceDownstream", better_metric):
        '''
        @type better_metric: AssertMetric
        '''
        state_refresh_interval = better_metric.state_refresh_interval
        if state_refresh_interval is None:
            # event caused by AssertMsg
            assert_timer_value = pim_globals.ASSERT_TIME
        else:
            # event caused by State Refresh Msg
            assert_timer_value = state_refresh_interval*3

        interface.set_assert_timer(assert_timer_value)
        interface.set_assert_winner_metric(better_metric)
        interface.set_assert_state(AssertState.Loser)

        interface.send_prune(holdtime=assert_timer_value)
        print('receivedPreferedMetric, W -> L')

    @staticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", state_refresh_interval):
        interface.set_assert_timer(state_refresh_interval*3)

    @staticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        #interface.assert_state = AssertState.NoInfo
        interface.set_assert_state(AssertState.NoInfo)
        interface.set_assert_winner_metric(AssertMetric.infinite_assert_metric())

        print('assertTimerExpires, W -> NI')

    @staticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        interface.send_assert_cancel()

        #interface.assert_timer.stop()
        interface.clear_assert_timer()

        #interface.assert_state = AssertState.NoInfo
        interface.set_assert_state(AssertState.NoInfo)

        interface.set_assert_winner_metric(AssertMetric.infinite_assert_metric())

        print('couldAssertIsNowFalse, W -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        pass


class LoserState(AssertStateABC):
    '''
    I am Assert Loser (L)
    This router has lost an (S,G) Assert on interface I. It must not
    forward packets from S destined for G onto interface I.
    '''

    @staticmethod
    def receivedDataFromDownstreamIf(interface: "TreeInterfaceDownstream"):
        """
        @type interface: TreeInterface
        """
        print('receivedDataFromDownstreamIf, L -> L')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        print('receivedInferiorMetricFromWinner, L -> NI')

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        print(
            'receivedInferiorMetricFromNonWinner_couldAssertIsTrue, L -> L')

    @staticmethod
    def receivedPreferedMetric(interface: "TreeInterfaceDownstream", better_metric):
        '''
        @type better_metric: AssertMetric
        '''
        state_refresh_interval = better_metric.state_refresh_interval
        if state_refresh_interval is None:
            assert_timer_value = pim_globals.ASSERT_TIME
        else:
            assert_timer_value = state_refresh_interval*3

        interface.set_assert_timer(assert_timer_value)

        #has_winner_changed = interface.assert_winner_metric.node != better_metric.node

        interface.set_assert_winner_metric(better_metric)

        if interface.could_assert():
            # todo enviar holdtime = assert_timer_value???!
            interface.send_prune(holdtime=assert_timer_value)

        print('receivedPreferedMetric, L -> L')

    @staticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", time):
        assert False, "this should never ocurr"

    @staticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        if interface.could_assert():
            interface.evaluate_ingroup()
        print('assertTimerExpires, L -> NI')

    @staticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        print('couldAssertIsNowFalse, L -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        print('couldAssertIsNowTrue, L -> NI')

    @staticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        print('winnerLivelinessTimerExpires, L -> NI')

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        interface.send_assert()

        print('receivedPruneOrJoinOrGraft, L -> L')

    @staticmethod
    def _to_NoInfo(interface: "TreeInterfaceDownstream"):
        #interface.assert_timer.stop()
        interface.clear_assert_timer()
        interface.set_assert_state(AssertState.NoInfo)
        interface.set_assert_winner_metric(AssertMetric.infinite_assert_metric())


class AssertState():
    NoInfo = NoInfoState()
    Winner = WinnerState()
    Loser = LoserState()
