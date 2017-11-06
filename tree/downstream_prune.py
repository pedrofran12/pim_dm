from abc import ABCMeta, abstractstaticmethod

from tree import globals as pim_globals
from utils import TYPE_CHECKING
if TYPE_CHECKING:
    from .tree_if_downstream import TreeInterfaceDownstream

class DownstreamStateABS(metaclass=ABCMeta):
    @abstractstaticmethod
    def receivedPrune(interface: "TreeInterfaceDownstream", holdtime):
        """
        Receive Prune(S,G)

        @type interface: Downstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: Downstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream"):
        """
        Receive Graft(S,G)

        @type interface: Downstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream", prune_holdtime):
        """
        PPT(S,G) Expires

        @type interface: Downstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: Downstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: Downstream
        """
        raise NotImplementedError()

    @abstractstaticmethod
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

        interface.set_prune_state(DownstreamState.PrunePending)

        time = 0
        if len(interface.get_interface().neighbors) > 1:
            time = pim_globals.JT_OVERRIDE_INTERVAL

        #timer = interface.get_ppt().start(time)
        interface.set_prune_pending_timer(time)


        print("receivedPrune, NI -> PP")

    @staticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """

        # Do nothing
        print("receivedJoin, NI -> NI")

    @staticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream"):
        """
        Receive Graft(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        # todo why pt stop???!!!
        #interface.get_pt().stop()

        interface.send_graft_ack()

        print('receivedGraft, NI -> NI')

    @staticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream", prune_holdtime):
        """
        PPT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False
        return

    @staticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False
        return

    @staticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        pass

        # Do nothing

    @staticmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        pass

        # Do nothing


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

        print('receivedPrune, PP -> PP')

    @staticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """

        #interface.get_ppt().stop()
        interface.clear_prune_pending_timer()

        interface.set_prune_state(DownstreamState.NoInfo)

        print('receivedJoin, PP -> NI')

    @staticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream"):
        """
        Receive Graft(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        # todo why prune timer and not prune pending timer???!
        #interface.get_pt().stop()
        interface.clear_prune_pending_timer()

        interface.set_prune_state(DownstreamState.NoInfo)
        interface.send_graft_ack()

        print('receivedGraft, PP -> NI')

    @staticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream", prune_holdtime):
        """
        PPT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """

        interface.set_prune_state(DownstreamState.Pruned)

        #pt = interface.get_pt()
        #pt.start(interface.get_lpht() - pim_globals.JT_OVERRIDE_INTERVAL)
        #interface.set_prune_timer(prune_holdtime - pim_globals.JT_OVERRIDE_INTERVAL)
        interface.set_prune_timer(interface.get_received_prune_holdtime() - pim_globals.JT_OVERRIDE_INTERVAL)


        interface.send_pruneecho()

        print('PPTexpires, PP -> P')

    @staticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """

        #assert False
        return

    @staticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: TreeInterfaceDownstreamDownstream
        """

        # todo understand better
        #interface.get_ppt().stop()
        interface.clear_prune_pending_timer()

        interface.set_prune_state(DownstreamState.NoInfo)

        print('is_now_RPF_Interface, PP -> NI')

    @staticmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        pass


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
        # todo ppt???! should be pt
        #ppt = interface.get_ppt()
        #if interface.get_lpht() > ppt.time_left():
        #    ppt.set_timer(interface.get_lpht())
        #    ppt.reset()
        # todo nao percebo... corrigir 0
        #if holdtime > 0:
        if interface.get_received_prune_holdtime() > interface.remaining_prune_timer():
            interface.set_prune_timer(holdtime)

        print('receivedPrune, P -> P')

    @staticmethod
    def receivedJoin(interface: "TreeInterfaceDownstream"):
        """
        Receive Join(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """

        #interface.get_pt().stop()
        interface.clear_prune_timer()

        interface.set_prune_state(DownstreamState.NoInfo)

        print('receivedPrune, P -> NI')

    @staticmethod
    def receivedGraft(interface: "TreeInterfaceDownstream"):
        """
        Receive Graft(S,G)

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #interface.get_pt().stop()
        interface.clear_prune_timer()
        interface.set_prune_state(DownstreamState.NoInfo)
        interface.send_graft_ack()

        print('receivedGraft, P -> NI')

    @staticmethod
    def PPTexpires(interface: "TreeInterfaceDownstream", prune_holdtime):
        """
        PPT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """
        #assert False
        return

    @staticmethod
    def PTexpires(interface: "TreeInterfaceDownstream"):
        """
        PT(S,G) Expires

        @type interface: TreeInterfaceDownstreamDownstream
        """

        interface.set_prune_state(DownstreamState.NoInfo)

        print('PTexpires, P -> NI')

    @staticmethod
    def is_now_RPF_Interface(interface: "TreeInterfaceDownstream"):
        """
        RPF_Interface(S) becomes I

        @type interface: TreeInterfaceDownstreamDownstream
        """
        # todo ver melhor
        #interface.get_pt().stop()
        interface.clear_prune_timer()
        interface.set_prune_state(DownstreamState.NoInfo)

        print('is_now_RPF_Interface, P -> NI')

    @staticmethod
    def send_state_refresh(interface: "TreeInterfaceDownstream"):
        """
        Send State Refresh(S,G) out I

        @type interface: TreeInterfaceDownstreamDownstream
        """

        #pt = interface.get_pt()
        #pt.set_timer(interface.get_lpht())
        #pt.reset()
        #interface.set_prune_timer(interface.get_lpht())
        interface.set_prune_timer(interface.get_received_prune_holdtime())

        print('send_state_refresh, P -> P')


class DownstreamState():
    NoInfo = NoInfo()
    Pruned = Pruned()
    PrunePending = PrunePending()
