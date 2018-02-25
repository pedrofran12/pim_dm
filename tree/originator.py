from abc import ABCMeta, abstractstaticmethod

from tree import globals as pim_globals

class OriginatorStateABC(metaclass=ABCMeta):
    @abstractstaticmethod
    def recvDataMsgFromSource(tree):
        pass

    @abstractstaticmethod
    def SRTexpires(tree):
        pass

    @abstractstaticmethod
    def SATexpires(tree):
        pass

    @abstractstaticmethod
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
        tree.set_state_refresh_timer()
        tree.create_state_refresh_msg()
        #print('SRT expired, O to O')
        tree.originator_logger.debug('SRT expired, O -> O')

    @staticmethod
    def SATexpires(tree):
        tree.clear_state_refresh_timer()
        tree.set_originator_state(OriginatorState.NotOriginator)

        #print('SAT expired, O to NO')
        tree.originator_logger.debug('SAT expired, O -> NO')

    @staticmethod
    def SourceNotConnected(tree):
        tree.clear_state_refresh_timer()
        tree.clear_source_active_timer()
        tree.set_originator_state(OriginatorState.NotOriginator)

        #print('Source no longer directly connected, O to NO')
        tree.originator_logger.debug('Source no longer directly connected, O -> NO')

    def __str__(self):
        return 'O'

class NotOriginator(OriginatorStateABC):
    @staticmethod
    def recvDataMsgFromSource(tree):
        '''
        @type interface: Tree
        '''
        tree.set_originator_state(OriginatorState.Originator)

        tree.set_state_refresh_timer()
        tree.set_source_active_timer()

        #print('new DataMsg from Source, NO to O')
        tree.originator_logger.debug('new DataMsg from Source, NO -> O')

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
        return 'NO'


class OriginatorState():
    NotOriginator = NotOriginator()
    Originator = Originator()
