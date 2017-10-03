from abc import ABCMeta, abstractstaticmethod


class SFMRAssertABC(metaclass=ABCMeta):
    @abstractstaticmethod
    def data_arrival(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()

    @staticmethod
    def recv_better_metric(interface, metric):
        '''
        @type interface: SFRMNonRootInterface
        @type metric: SFMRAssertMetric
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def recv_worse_metric(interface, metric):
        '''
        @type interface: SFRMNonRootInterface
        @type metric: SFMRAssertMetric
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def aw_failure(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def al_rpc_better_than_aw(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def aw_rpc_worsens(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def recv_reset(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()

    @abstractstaticmethod
    def is_now_pruned(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplemented()


class SFMRAssertWinner(SFMRAssertABC):
    @staticmethod
    def data_arrival(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('data_arrival, W -> W')
        interface.send_assert()

    @staticmethod
    def recv_better_metric(interface, metric):
        '''
        @type interface: SFRMNonRootInterface
        @type metric: SFMRAssertMetric
        '''
        print('recv_better_metric, W -> L')

        interface._set_assert_state(AssertState.Looser)
        interface._set_winner_metric(metric)

    @staticmethod
    def recv_worse_metric(interface, metric):
        '''
        @type interface: SFRMNonRootInterface
        @type metric: SFMRAssertMetric
        '''
        print('recv_worse_metric, W -> W')

        interface.send_assert()

    @staticmethod
    def aw_failure(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        assert False

    @staticmethod
    def al_rpc_better_than_aw(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        assert False

    @staticmethod
    def aw_rpc_worsens(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        interface.send_reset()
        print('aw_rpc_worsens, W -> W')

    @staticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_root, W -> W')

        interface.send_reset()

    @staticmethod
    def recv_reset(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('recv_reset, W -> W')

    @staticmethod
    def is_now_pruned(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_pruned, W -> W')


class SFMRAssertLooser(SFMRAssertABC):
    @staticmethod
    def data_arrival(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('data_arrival, L -> L')

    @staticmethod
    def recv_better_metric(interface, metric):
        '''
        @type interface: SFRMNonRootInterface
        @type metric: SFMRAssertMetric
        '''
        print('recv_better_metric, L -> L')

        interface._set_winner_metric(metric)

    @staticmethod
    def recv_worse_metric(interface, metric):
        '''
        @type interface: SFRMNonRootInterface
        @type metric: SFMRAssertMetric
        '''
        print('recv_worse_metric, L -> W')

        interface.send_assert()
        interface._set_assert_state(AssertState.Winner)
        interface._set_winner_metric(None)

    @staticmethod
    def aw_failure(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('aw_failure, L -> W')

        interface._set_assert_state(AssertState.Winner)
        interface._set_winner_metric(None)
        interface.send_assert()

    @staticmethod
    def al_rpc_better_than_aw(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('al_rpc_improves, L -> W')

        interface._set_assert_state(AssertState.Winner)
        interface._set_winner_metric(None)
        interface.send_assert()


    @staticmethod
    def aw_rpc_worsens(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        assert False

    @staticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_root, L -> L')

    @staticmethod
    def recv_reset(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('recv_reset, L -> W')

        interface._set_assert_state(AssertState.Winner)
        interface._set_winner_metric(None)


    @staticmethod
    def is_now_pruned(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_pruned, L -> W')

        interface._set_assert_state(AssertState.Winner)
        interface._set_winner_metric(None)


class AssertState():
    Winner = SFMRAssertWinner()
    Looser = SFMRAssertLooser()
