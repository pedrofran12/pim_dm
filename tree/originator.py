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
        print('SRT expired, O to O')

        tree.set_state_refresh_timer()
        tree.create_state_refresh_msg()

    @staticmethod
    def SATexpires(tree):
        print('SAT expired, O to NO')

        tree.clear_state_refresh_timer()
        tree.set_originator_state(OriginatorState.NotOriginator)

    @staticmethod
    def SourceNotConnected(tree):
        print('Source no longer directly connected, O to NO')

        tree.clear_state_refresh_timer()
        tree.clear_source_active_timer()
        tree.set_originator_state(OriginatorState.NotOriginator)


class NotOriginator(OriginatorStateABC):
    @staticmethod
    def recvDataMsgFromSource(tree):
        '''
        @type interface: Tree
        '''
        tree.set_originator_state(OriginatorState.Originator)

        tree.set_state_refresh_timer()
        tree.set_source_active_timer()

        print('new DataMsg from Source, NO to O')

    @staticmethod
    def SRTexpires(tree):
        assert False

    @staticmethod
    def SATexpires(tree):
        assert False

    @staticmethod
    def SourceNotConnected(tree):
        return


class OriginatorState():
    NotOriginator = NotOriginator()
    Originator = Originator()
