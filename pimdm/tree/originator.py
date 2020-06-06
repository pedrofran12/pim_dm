from abc import ABCMeta, abstractmethod


class OriginatorStateABC(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def recvDataMsgFromSource(tree):
        pass

    @staticmethod
    @abstractmethod
    def SRTexpires(tree):
        pass

    @staticmethod
    @abstractmethod
    def SATexpires(tree):
        pass

    @staticmethod
    @abstractmethod
    def SourceNotConnected(tree):
        pass


class Originator(OriginatorStateABC):
    @staticmethod
    def recvDataMsgFromSource(tree):
        tree.set_source_active_timer()

    @staticmethod
    def SRTexpires(tree):
        '''
        @type tree: Tree
        '''
        tree.originator_logger.debug('SRT expired, O -> O')
        tree.set_state_refresh_timer()
        tree.create_state_refresh_msg()

    @staticmethod
    def SATexpires(tree):
        tree.originator_logger.debug('SAT expired, O -> NO')
        tree.clear_state_refresh_timer()
        tree.set_originator_state(OriginatorState.NotOriginator)

    @staticmethod
    def SourceNotConnected(tree):
        tree.originator_logger.debug('Source no longer directly connected, O -> NO')
        tree.clear_state_refresh_timer()
        tree.clear_source_active_timer()
        tree.set_originator_state(OriginatorState.NotOriginator)

    def __str__(self):
        return 'Originator'

class NotOriginator(OriginatorStateABC):
    @staticmethod
    def recvDataMsgFromSource(tree):
        '''
        @type interface: Tree
        '''
        tree.originator_logger.debug('new DataMsg from Source, NO -> O')
        tree.set_originator_state(OriginatorState.Originator)

        tree.set_state_refresh_timer()
        tree.set_source_active_timer()

    @staticmethod
    def SRTexpires(tree):
        assert False, "SRTexpires in NO"

    @staticmethod
    def SATexpires(tree):
        assert False, "SATexpires in NO"

    @staticmethod
    def SourceNotConnected(tree):
        return

    def __str__(self):
        return 'NotOriginator'


class OriginatorState():
    NotOriginator = NotOriginator()
    Originator = Originator()
