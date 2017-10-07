from abc import ABCMeta, abstractstaticmethod

from tree import globals as pim_globals

class OriginatorStateABC(metaclass=ABCMeta):
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
        tree.source_active_timer.reset()

    @staticmethod
    def SRTexpires(tree):
        '''
        @type tree: Tree
        '''
        tree.rprint('SRT expired, O to O')

        tree.state_refresh_timer.reset()
        tree.send_state_refresh_msg()

    @staticmethod
    def SATexpires(tree):
        tree.rprint('SAT expired, O to NO')

        tree.source_active_timer.stop()
        tree.state_refresh_timer.stop()
        tree.originator_state = OriginatorState.NotOriginator

    @staticmethod
    def SourceNotConnected(tree):
        tree.rprint('Source no longer directly connected, O to NO')

        tree.source_active_timer.stop()
        tree.state_refresh_timer.stop()
        tree.originator_state = OriginatorState.NotOriginator


class NotOriginator(OriginatorStateABC):
    @staticmethod
    def recvDataMsgFromSource(tree):
        '''
        @type interface: Tree
        '''
        tree.originator_state = OriginatorState.Originator

        tree.state_refresh_timer.start()
        tree.source_active_timer.start()

        tree.rprint('new DataMsg from Source, NO to O')
        # Since the recording of the TTL is common to both states,its registering is made on the
        # Tree.new_state_refresh_msg(...) method

    @staticmethod
    def SRTexpires(tree):
        assert False

    @staticmethod
    def SATexpires(tree):
        assert False

    @staticmethod
    def SourceNotConnected(tree):
        pass


class OriginatorState():
    NotOriginator = NotOriginator()
    Originator = Originator()
