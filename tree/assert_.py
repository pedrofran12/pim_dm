from abc import ABCMeta, abstractmethod

import tree.globals as pim_globals
from .metric import AssertMetric
from utils import TYPE_CHECKING
if TYPE_CHECKING:
    from .tree_if_downstream import TreeInterfaceDownstream


class AssertStateABC(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def receivedDataFromDownstreamIf(interface: "TreeInterfaceDownstream"):
        """
        An (S,G) Data packet received on downstream interface

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        """
        Receive Inferior (Assert OR State Refresh) from Assert Winner

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        """
        Receive Inferior (Assert OR  State Refresh) from non-Assert Winner
        AND CouldAssert==TRUE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def receivedPreferedMetric(interface: "TreeInterfaceDownstream", better_metric):
        """
        Receive Preferred Assert OR State Refresh

        @type interface: TreeInterface
        @type better_metric: AssertMetric
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", time):
        """
        Send State Refresh


        @type interface: TreeInterface
        @type time: int
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        """
        AT(S,G) Expires

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        """
        CouldAssert -> FALSE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        """
        CouldAssert -> TRUE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        """
        Winner’s NLT(N,I) Expires

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        """
        Receive Prune(S,G), Join(S,G) or Graft(S,G)

        @type interface: TreeInterface
        """
        raise NotImplementedError()


    def _sendAssert_setAT(interface: "TreeInterfaceDownstream"):
        interface.set_assert_timer(pim_globals.ASSERT_TIME)
        interface.send_assert()


    # Override
    def __str__(self) -> str:
        return "AssertSM:" + self.__class__.__name__


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
        interface.set_assert_winner_metric(interface.my_assert_metric())
        interface.set_assert_state(AssertState.Winner)

        NoInfoState._sendAssert_setAT(interface)

        #print('receivedDataFromDownstreamIf, NI -> W')
        interface.assert_logger.debug('receivedDataFromDownstreamIf, NI -> W')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        interface.set_assert_winner_metric(interface.my_assert_metric())
        interface.set_assert_state(AssertState.Winner)

        NoInfoState._sendAssert_setAT(interface)

        #print('receivedInferiorMetricFromNonWinner_couldAssertIsTrue, NI -> W')
        interface.assert_logger.debug('receivedInferiorMetricFromNonWinner_couldAssertIsTrue, NI -> W')

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

        #print('receivedPreferedMetric, NI -> L')
        interface.assert_logger.debug('receivedPreferedMetric, NI -> L')

    @staticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", time):
        pass

    @staticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        #print('couldAssertIsNowFalse, NI -> NI')
        interface.assert_logger.debug('couldAssertIsNowFalse, NI -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        #print('couldAssertIsNowTrue, NI -> NI')
        interface.assert_logger.debug('couldAssertIsNowTrue, NI -> NI')

    @staticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        #print('receivedPruneOrJoinOrGraft, NI -> NI')
        interface.assert_logger.debug('receivedPruneOrJoinOrGraft, NI -> NI')

    def __str__(self) -> str:
        return "NoInfo"


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

        #print('receivedDataFromDownstreamIf, W -> W')
        interface.assert_logger.debug('receivedDataFromDownstreamIf, W -> W')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        WinnerState._sendAssert_setAT(interface)

        #print('receivedInferiorMetricFromNonWinner_couldAssertIsTrue, W -> W')
        interface.assert_logger.debug('receivedInferiorMetricFromNonWinner_couldAssertIsTrue, W -> W')

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
        #print('receivedPreferedMetric, W -> L')
        interface.assert_logger.debug('receivedPreferedMetric, W -> L')

    @staticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", state_refresh_interval):
        interface.set_assert_timer(state_refresh_interval*3)

    @staticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        interface.set_assert_winner_metric(AssertMetric.infinite_assert_metric())
        interface.set_assert_state(AssertState.NoInfo)

        #print('assertTimerExpires, W -> NI')
        interface.assert_logger.debug('assertTimerExpires, W -> NI')

    @staticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        interface.send_assert_cancel()

        interface.clear_assert_timer()

        interface.set_assert_winner_metric(AssertMetric.infinite_assert_metric())
        interface.set_assert_state(AssertState.NoInfo)

        #print('couldAssertIsNowFalse, W -> NI')
        interface.assert_logger.debug('couldAssertIsNowFalse, W -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        pass

    def __str__(self) -> str:
        return "Winner"



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
        #print('receivedDataFromDownstreamIf, L -> L')
        interface.assert_logger.debug('receivedDataFromDownstreamIf, L -> L')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        #print('receivedInferiorMetricFromWinner, L -> NI')
        interface.assert_logger.debug('receivedInferiorMetricFromWinner, L -> NI')

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface: "TreeInterfaceDownstream"):
        #print('receivedInferiorMetricFromNonWinner_couldAssertIsTrue, L -> L')
        interface.assert_logger.debug('receivedInferiorMetricFromNonWinner_couldAssertIsTrue, L -> L')

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
        interface.set_assert_winner_metric(better_metric)
        interface.set_assert_state(AssertState.Loser)

        if interface.could_assert():
            interface.send_prune(holdtime=assert_timer_value)

        #print('receivedPreferedMetric, L -> L')
        interface.assert_logger.debug('receivedPreferedMetric, L -> L')

    @staticmethod
    def sendStateRefresh(interface: "TreeInterfaceDownstream", time):
        assert False, "this should never ocurr"

    @staticmethod
    def assertTimerExpires(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)
        #print('assertTimerExpires, L -> NI')
        interface.assert_logger.debug('assertTimerExpires, L -> NI')

    @staticmethod
    def couldAssertIsNowFalse(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)
        #print('couldAssertIsNowFalse, L -> NI')
        interface.assert_logger.debug('couldAssertIsNowFalse, L -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)
        #print('couldAssertIsNowTrue, L -> NI')
        interface.assert_logger.debug('couldAssertIsNowTrue, L -> NI')

    @staticmethod
    def winnerLivelinessTimerExpires(interface: "TreeInterfaceDownstream"):
        LoserState._to_NoInfo(interface)

        #print('winnerLivelinessTimerExpires, L -> NI')
        interface.assert_logger.debug('winnerLivelinessTimerExpires, L -> NI')

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface: "TreeInterfaceDownstream"):
        interface.send_assert()

        #print('receivedPruneOrJoinOrGraft, L -> L')
        interface.assert_logger.debug('receivedPruneOrJoinOrGraft, L -> L')

    @staticmethod
    def _to_NoInfo(interface: "TreeInterfaceDownstream"):
        interface.clear_assert_timer()
        interface.set_assert_winner_metric(AssertMetric.infinite_assert_metric())
        interface.set_assert_state(AssertState.NoInfo)

    def __str__(self) -> str:
        return "Loser"

class AssertState():
    NoInfo = NoInfoState()
    Winner = WinnerState()
    Loser = LoserState()
