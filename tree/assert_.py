from abc import ABCMeta, abstractstaticmethod

import tree.globals as pim_globals
from .metric import AssertMetric


class AssertStateABC(metaclass=ABCMeta):
    @abstractstaticmethod
    def receivedDataFromDownstreamIf(interface):
        """
        An (S,G) Data packet received on downstream interface

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedInferiorMetricFromWinner(interface):
        """
        Receive Inferior (Assert OR State Refresh) from Assert Winner

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface):
        """
        Receive Inferior (Assert OR  State Refresh) from non-Assert Winner
        AND CouldAssert==TRUE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedPreferedMetric(interface, assert_time, better_metric):
        """
        Receive Preferred Assert OR State Refresh

        @type interface: TreeInterface
        @type assert_time: int
        @type better_metric: AssertMetric
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def sendStateRefresh(interface, time):
        """
        Send State Refresh


        @type interface: TreeInterface
        @type time: int
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def assertTimerExpires(interface):
        """
        AT(S,G) Expires

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def couldAssertIsNowFalse(interface):
        """
        CouldAssert -> FALSE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def couldAssertIsNowTrue(interface):
        """
        CouldAssert -> TRUE

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def winnerLivelinessTimerExpires(interface):
        """
        Winner’s NLT(N,I) Expires

        @type interface: TreeInterface
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedPruneOrJoinOrGraft(interface):
        """
        Receive Prune(S,G), Join(S,G) or Graft(S,G)

        @type interface: TreeInterface
        """
        raise NotImplementedError()


    def _sendAssert_setAT(interface):
        interface.send_assert()

        interface.assert_timer.set_timer(pim_globals.ASSERT_TIME)
        interface.assert_timer.reset()

    @staticmethod
    def rprint(interface, msg, *entrys):
        '''
        Method used for simplifiyng the process of reporting changes in a assert state
        Tree Interface.
        @type interface: TreeInterface
        '''
        interface.rprint(msg, 'assert state', *entrys)

    # Override
    def __str__(self) -> str:
        return "PruneSM:" + self.__class__.__name__


class LoserState(AssertStateABC):
    '''
    I am Assert Loser (L)
    This router has lost an (S,G) Assert on interface I. It must not
    forward packets from S destined for G onto interface I.
    '''

    @staticmethod
    def receivedDataFromDownstreamIf(interface):
        """
        @type interface: TreeInterface
        """
        interface.rprint('receivedDataFromDownstreamIf, L -> L')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface):
        LoserState._to_NoInfo(interface)

        interface.rprint('receivedInferiorMetricFromWinner, L -> NI')

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface):
        interface.rprint(
            'receivedInferiorMetricFromNonWinner_couldAssertIsTrue, L -> L')

    @staticmethod
    def receivedPreferedMetric(interface, assert_time, better_metric):
        '''
        @type better_metric: AssertMetric
        '''
        interface.assert_timer.set_timer(assert_time)
        interface.assert_timer.reset()

        has_winner_changed = interface.assert_winner_metric.node != better_metric.node

        interface.assert_winner_metric = better_metric

        if interface.could_assert() and has_winner_changed:
            interface.send_prune()

        interface.rprint('receivedPreferedMetric, L -> L', 'from:',
                         better_metric.node)

    @staticmethod
    def sendStateRefresh(interface, time):
        assert False, "this should never ocurr"

    @staticmethod
    def assertTimerExpires(interface):
        LoserState._to_NoInfo(interface)

        interface.rprint('assertTimerExpires, L -> NI')

    @staticmethod
    def couldAssertIsNowFalse(interface):
        LoserState._to_NoInfo(interface)

        interface.rprint('couldAssertIsNowFalse, L -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface):
        LoserState._to_NoInfo(interface)

        interface.rprint('couldAssertIsNowTrue, L -> NI')

    @staticmethod
    def winnerLivelinessTimerExpires(interface):
        LoserState._to_NoInfo(interface)

        interface.rprint('winnerLivelinessTimerExpires, L -> NI')

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface):
        interface.send_assert()

        interface.rprint('receivedPruneOrJoinOrGraft, L -> L')

    @staticmethod
    def _to_NoInfo(interface):
        interface.assert_timer.stop()
        interface.assert_state = AssertState.NoInfo
        interface.assert_winner_metric = AssertMetric.infinite_assert_metric()


class NoInfoState(AssertStateABC):
    '''
    NoInfoState (NI)
    This router has no (S,G) Assert state on interface I.
    '''

    @staticmethod
    def receivedDataFromDownstreamIf(interface):
        """
        @type interface: TreeInterface
        """
        NoInfoState._sendAssert_setAT(interface)

        interface.assert_state = AssertState.Winner
        interface.assert_winner_metric = interface.assert_metric

        interface.rprint('receivedDataFromDownstreamIf, NI -> W')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface):
        NoInfoState._sendAssert_setAT(interface)

        interface.assert_state = AssertState.Winner
        interface.assert_winner_metric = interface.assert_metric

        interface.rprint(
            'receivedInferiorMetricFromNonWinner_couldAssertIsTrue, NI -> W')

    @staticmethod
    def receivedPreferedMetric(interface, assert_time, better_metric):
        '''
        @type interface: TreeInterface
        '''
        interface.assert_timer.set_timer(assert_time)
        interface.assert_timer.reset()

        interface.assert_state = AssertState.Loser
        interface.assert_winner_metric = better_metric

        if interface.could_assert():
            interface.send_prune()

        interface.rprint('receivedPreferedMetric, NI -> L')

    @staticmethod
    def sendStateRefresh(interface, time):
        pass

    @staticmethod
    def assertTimerExpires(interface):
        assert False, "this should never ocurr"

    @staticmethod
    def couldAssertIsNowFalse(interface):
        interface.rprint('couldAssertIsNowFalse, NI -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface):
        interface.rprint('couldAssertIsNowTrue, NI -> NI')

    @staticmethod
    def winnerLivelinessTimerExpires(interface):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface):
        interface.rprint('receivedPruneOrJoinOrGraft, NI -> NI')


class WinnerState(AssertStateABC):
    '''
    I am Assert Winner (W)
    This router has won an (S,G) Assert on interface I. It is now
    responsible for forwarding traffic from S destined for G via
    interface I.
    '''

    @staticmethod
    def receivedDataFromDownstreamIf(interface):
        """
        @type interface: TreeInterface
        """
        WinnerState._sendAssert_setAT(interface)

        interface.rprint('receivedDataFromDownstreamIf, W -> W')

    @staticmethod
    def receivedInferiorMetricFromWinner(interface):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedInferiorMetricFromNonWinner_couldAssertIsTrue(interface):
        WinnerState._sendAssert_setAT(interface)

        interface.rprint(
            'receivedInferiorMetricFromNonWinner_couldAssertIsTrue, W -> W')

    @staticmethod
    def receivedPreferedMetric(interface, assert_time, better_metric):
        '''
        @type better_metric: AssertMetric
        '''

        interface.assert_timer.set_timer(assert_time)
        interface.assert_timer.reset()

        interface.assert_winner_metric = better_metric

        interface.assert_state = AssertState.Loser

        if interface.could_assert:
            interface.send_prune()

        interface.rprint('receivedPreferedMetric, W -> L', 'from:',
                         str(better_metric.node))

    @staticmethod
    def sendStateRefresh(interface, time):
        interface.assert_timer.set_timer(time)
        interface.assert_timer.reset()

    @staticmethod
    def assertTimerExpires(interface):
        interface.assert_state = AssertState.NoInfo
        interface.assert_winner_metric = AssertMetric.infinite_assert_metric()

        interface.rprint('assertTimerExpires, W -> NI')

    @staticmethod
    def couldAssertIsNowFalse(interface):
        interface.send_assert_cancel()

        interface.assert_timer.stop()

        interface.assert_state = AssertState.NoInfo
        interface.assert_winner_metric = AssertMetric.infinite_assert_metric()

        interface.rprint('couldAssertIsNowFalse, W -> NI')

    @staticmethod
    def couldAssertIsNowTrue(interface):
        assert False, "this should never ocurr"

    @staticmethod
    def winnerLivelinessTimerExpires(interface):
        assert False, "this should never ocurr"

    @staticmethod
    def receivedPruneOrJoinOrGraft(interface):
        pass


class AssertState():
    NoInfo = NoInfoState()
    Winner = WinnerState()
    Loser = LoserState()
