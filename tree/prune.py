from abc import ABCMeta, abstractstaticmethod


class SFMRPruneStateABC(metaclass=ABCMeta):
    @abstractstaticmethod
    def recv_prune(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplementedError()

    @abstractstaticmethod
    def recv_join(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplementedError()

    @abstractstaticmethod
    def dipt_expires(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplementedError()

    @abstractstaticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplementedError()

    @abstractstaticmethod
    def new_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplementedError()

    @abstractstaticmethod
    def lost_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        raise NotImplementedError()


class SFMRDownstreamInterested(SFMRPruneStateABC):
    @staticmethod
    def recv_prune(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''

        if len(interface.get_interface().neighbors) <= 1:
            print('recv_prune, DI -> NDI (only 1 nbr)')
            interface._set_prune_state(SFMRPruneState.NDI)

        else:
            print('recv_prune, DI -> DIP')
            interface._set_prune_state(SFMRPruneState.DIP)
            #interface._get_dipt().start()
            interface.set_dipt_timer()

    @staticmethod
    def recv_join(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('recv_join, DI -> DI')

    @staticmethod
    def dipt_expires(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        assert False

    @staticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_root, DI -> DI')

    @staticmethod
    def new_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('new_nbr, DI -> N')

    @staticmethod
    def lost_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('lost_nbr, DI -> DIP')

        interface.send_prune()
        interface._set_prune_state(SFMRPruneState.DIP)
        #interface._get_dipt().start()
        interface.set_dipt_timer()


class SFMRDownstreamInterestedPending(SFMRPruneStateABC):
    @staticmethod
    def recv_prune(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        # TODO foi alterado pelo Pedro... necessita de verificacao se esta OK...
        #print('recv_prune, DIP -> DIP')
        if len(interface.get_interface().neighbors) <= 1:
            print('recv_prune, DIP -> NDI (only 1 nbr)')
            interface._set_prune_state(SFMRPruneState.NDI)
            interface.clear_dipt_timer()
        else:
            print('recv_prune, DIP -> DIP')

    @staticmethod
    def recv_join(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('recv_join, DIP -> DI')

        interface._set_prune_state(SFMRPruneState.DI)
        interface.clear_dipt_timer()

    @staticmethod
    def dipt_expires(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('dipt_expires, DIP -> NDI')

        interface._set_prune_state(SFMRPruneState.NDI)

    @staticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_root, DIP -> DI')

        interface._set_prune_state(SFMRPruneState.DI)
        #interface._get_dipt().stop()
        interface.clear_dipt_timer()

    @staticmethod
    def new_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('new_nbr, DIP -> DIP')

        interface.send_prune()
        #interface._get_dipt().reset()
        interface.set_dipt_timer()

    @staticmethod
    def lost_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('lost_nbr, DIP -> DIP')
        #todo alterado pelo Pedro... necessita de verificar se esta OK...
        #interface.send_prune()
        #interface.set_dipt_timer()


class SFMRNoDownstreamInterested(SFMRPruneStateABC):
    @staticmethod
    def recv_prune(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('recv_prune, NDI -> NDI')

    @staticmethod
    def recv_join(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('recv_join, NDI -> DI')

        interface._set_prune_state(SFMRPruneState.DI)
        #interface._get_dipt().stop()
        interface.clear_dipt_timer()

    @staticmethod
    def dipt_expires(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        assert False

    @staticmethod
    def is_now_root(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('is_now_root, NDI -> DI')

        interface._set_prune_state(SFMRPruneState.DI)

    @staticmethod
    def new_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('new_nbr, NDI -> NDI')

        interface.send_prune()

    @staticmethod
    def lost_nbr(interface):
        '''
        @type interface: SFRMNonRootInterface
        '''
        print('lost_nbr, NDI -> NDI')


class SFMRPruneState():
    DI = SFMRDownstreamInterested()
    DIP = SFMRDownstreamInterestedPending()
    NDI = SFMRNoDownstreamInterested()
