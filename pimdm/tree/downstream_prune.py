from abc import ABCMeta, abstractmethod

from . import pim_globals as pim_globals
from pimdm.utils import TYPE_CHECKING
if TYPE_CHECKING:
    from .tree_if_downstream import TreeInterfaceDownstream

class DownstreamStateABS(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def receivedPrune(interface: "TreeInterfaceDownstream", holdtime):
        """
        Receive Prune(S,G)

        @type interface: Downstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: Downstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def receivedGraft(interface: "TreeInterfaceDownstream", source_ip):
        """
        Receive Graft(S,G)

        @type interface: Downstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def PPTexpires(interface: "TreeInterfaceDownstream"):
        """
        PPT(S,G) Expires

        @type interface: Downstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: Downstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: Downstream
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: Downstream
        """
        raise NotImplementedError()

    def __str__(self):
        return "Downstream." + self.__class__.__name__


class NoInfo(DownstreamStateABS):
    '''
    NoInfo(NI)
    The interface has no (S,G) Prune state, and neither the Prune
    timer (PT(S,G,I)) nor the PrunePending timer ((PPT(S,G,I)) is
    running.
    '''

    @staticmethod
    def receivedPrune(interface: "TreeInterfaceDownstream", holdtime):
        """
        Receive Prune(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug("receivedPrune, NI -> PP")
        interface.set_prune_state(DownstreamState.PrunePending)

        time = 0
        if len(interface.get_interface().neighbors) > 1:
            time = pim_globals.JP_OVERRIDE_INTERVAL

        interface.set_prune_pending_timer(time)

    @staticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        # Do nothing
        interface.join_prune_logger.debug("receivedJoin, NI -> NI")

    @staticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream", source_ip):
        """
        Receive Graft(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedGraft, NI -> NI')
        interface.send_graft_ack(source_ip)

    @staticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream"):
        """
        PPT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False, "PPTexpires in state NI"
        return

    @staticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False, "PTexpires in state NI"
        return

    @staticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        # Do nothing
        return

    @staticmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        # Do nothing
        return

    def __str__(self):
        return "NoInfo"



class PrunePending(DownstreamStateABS):
    '''
    PrunePending(PP)
    The router has received a Prune(S,G) on this interface from a
    downstream neighbor and is waiting to see whether the prune will
    be overridden by another downstream router. For forwarding
    purposes, the PrunePending state functions exactly like the
    NoInfo state.
    '''

    @staticmethod
    def receivedPrune(interface: "TreeInterfaceDownstream", holdtime):
        """
        Receive Prune(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedPrune, PP -> PP')


    @staticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedJoin, PP -> NI')

        interface.clear_prune_pending_timer()

        interface.set_prune_state(DownstreamState.NoInfo)


    @staticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream", source_ip):
        """
        Receive Graft(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedGraft, PP -> NI')

        interface.clear_prune_pending_timer()

        interface.set_prune_state(DownstreamState.NoInfo)
        interface.send_graft_ack(source_ip)

    @staticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream"):
        """
        PPT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('PPTexpires, PP -> P')
        interface.set_prune_state(DownstreamState.Pruned)
        interface.set_prune_timer(interface.get_received_prune_holdtime() - pim_globals.JP_OVERRIDE_INTERVAL)

        if len(interface.get_interface().neighbors) > 1:
            interface.send_pruneecho()

    @staticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False, "PTexpires in state PP"
        return

    @staticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('is_now_RPF_Interface, PP -> NI')

        interface.clear_prune_pending_timer()

        interface.set_prune_state(DownstreamState.NoInfo)

    @staticmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        return

    def __str__(self):
        return "PrunePending"

class Pruned(DownstreamStateABS):
    '''
    Pruned(P)
    The router has received a Prune(S,G) on this interface from a
    downstream neighbor, and the Prune was not overridden. Data from
    S addressed to group G is no longer being forwarded on this
    interface.
    '''

    @staticmethod
    def receivedPrune(interface: "TreeInterfaceDownstream", holdtime):
        """
        Receive Prune(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedPrune, P -> P')
        if holdtime > interface.remaining_prune_timer():
            interface.set_prune_timer(holdtime)

    @staticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedPrune, P -> NI')

        interface.clear_prune_timer()

        interface.set_prune_state(DownstreamState.NoInfo)

    @staticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream", source_ip):
        """
        Receive Graft(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('receivedGraft, P -> NI')
        interface.clear_prune_timer()
        interface.set_prune_state(DownstreamState.NoInfo)
        interface.send_graft_ack(source_ip)

    @staticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream"):
        """
        PPT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False, "PPTexpires in state P"
        return

    @staticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('PTexpires, P -> NI')
        interface.set_prune_state(DownstreamState.NoInfo)

    @staticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger('is_now_RPF_Interface, P -> NI')
        interface.clear_prune_timer()
        interface.set_prune_state(DownstreamState.NoInfo)

    @staticmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        interface.join_prune_logger.debug('send_state_refresh, P -> P')
        if interface.get_interface().is_state_refresh_capable():
            interface.set_prune_timer(interface.get_received_prune_holdtime())

    def __str__(self):
        return "Pruned"

class DownstreamState():
    NoInfo = NoInfo()
    Pruned = Pruned()
    PrunePending = PrunePending()
