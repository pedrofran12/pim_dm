'''
Created on Jul 16, 2015

@author: alex
'''
from convergence import Convergence
from des.entities.node import NodeChanges
from des.event.timer import Timer
from sfmr.messages.state_reset import SFMRStateResetMsg
from sfmr.non_root_interface import SFRMNonRootInterface
from sfmr.root_interface import SFRMRootInterface
from sfmr.router_interface import SFMRInterface, NeighborEvent


class SFMRTree(object):
    TREE_TIMEOUT = 180

    def __init__(self, rprint, unicastd, tree_id, tree_liveliness_callback,
                 ifs, node, has_members):
        '''
        @type ifs: dict
        @type node: Node
        '''

        self._rpf_node = None
        self._rpf_link = None

        self._rprint = rprint
        self._tree_id = tree_id
        self._unicastd = unicastd
        self._node = node
        self._has_members = has_members
        self._was_in_group = True
        self._rpf_is_origin = False

        self._liveliness_timer = Timer(None, SFMRTree.TREE_TIMEOUT,
                                       self.___liveliness_timer_expired)
        self._died_cb = tree_liveliness_callback

        self._interfaces = dict()
        self._up_if = None

        self.set_rpf()

        self._create_root_if(self._rpf_link, ifs.pop(self._rpf_link))

        for k, v in ifs.items():
            self._create_non_root_if(k, v)

        self.rprint('Tree created')
        self.evaluate_ingroup()

        if self.is_originater():
            self._liveliness_timer.start()
            self.rprint('set SAT')

    def set_rpf(self):
        """
        Updates the reverse path forward node and link from the unicast daemon

        returning true if there is a change in the rpf_link

        @type unid: Unicast

        @rtype: (Bool, Bool)
        @return: The first bool indicates if rpf_link has changed
                 The second indicates if rpf_node has changed
        """

        next_hop_addr = self._unicastd.next_hop(self.get_source())

        node_has_changed = next_hop_addr.get_node() != self._rpf_node
        link_has_changed = next_hop_addr.get_link() != self._rpf_link

        self._rpf_node = next_hop_addr.get_node()
        self._rpf_link = next_hop_addr.get_link()

        if link_has_changed:
            self.rprint("Tree rpf link changed", 'to', self._rpf_link)

        return link_has_changed, node_has_changed

    def recv_data_msg(self, msg, sender):
        '''
        @type msg: DataMsg
        @type sender: Addr
        '''
        if self.is_originater():
            self._liveliness_timer.reset()

        self._interfaces[sender.get_link()].recv_data_msg(msg, sender)

        if sender.get_link() == self._rpf_link:
            for interface in self._interfaces.values():
                interface.forward_data_msg(msg)

    def recv_assert_msg(self, msg, sender):
        '''
        @type msg: SFMRAssertMsg
        @type sender: Addr
        '''
        self._interfaces[sender.get_link()].recv_assert_msg(msg, sender)

    def recv_reset_msg(self, msg, sender):
        '''
        @type msg: SFMResetMsg
        @type sender: Addr
        '''
        self._interfaces[sender.get_link()].recv_reset_msg(msg, sender)

    def recv_prune_msg(self, msg, sender):
        '''
        @type msg: SFMResetMsg
        @type sender: Addr
        '''

        self._interfaces[sender.get_link()].recv_prune_msg(
            msg, sender, self.is_in_group())

    def recv_join_msg(self, msg, sender):
        '''
        @type msg: SFMResetMsg
        @type sender: Addr
        '''
        self._interfaces[sender.get_link()].recv_join_msg(
            msg, sender, self.is_in_group())

    def recv_state_reset_msg(self, msg, sender):
        '''
        @type msg: SFMResetMsg
        @type sender: Addr
        '''
        self.flood_state_reset(msg)
        self._died_cb(self.get_tree_id())

    def ___liveliness_timer_expired(self):
        self.rprint('Tree liveliness timer expired')

        self.flood_state_reset(SFMRStateResetMsg(self.get_tree_id()))
        self._died_cb(self.get_tree_id())

    def flood_state_reset(self, msg):
        for interface in self._interfaces.values():
            interface.forward_state_reset_msg(msg)

    def network_update(self, change, args):
        assert isinstance(args, SFMRInterface)
        link = args.get_link()

        if NodeChanges.NewIf == change:
            self._create_non_root_if(link, args)

        elif NodeChanges.CrashIf == change:
            self._interfaces.pop(link).delete()

            if link == self._rpf_link:
                self._up_if = None

                if self._liveliness_timer.is_ticking():
                    self._liveliness_timer.stop()
                    self.rprint('stop SAT')

        elif NodeChanges.IfCostChange == change:
            pass

        else:
            assert False, "this should never be called (case switch)"

    def update(self, caller, arg):
        """ called when there is a change in the routing Daemons """
        link_ch, node_ch = self.set_rpf()

        if self._rpf_link is None:
            self.rprint('Lost unicast connection to source')
            self._died_cb(self.get_tree_id())
            return

        if link_ch:
            if self._up_if is not None:
                old_link = self._up_if.get_link()
                old_router_if = self._up_if.get_interface()

                self._interfaces.pop(old_link).delete()
                self._create_non_root_if(old_link, old_router_if)
                self._up_if = None

            rpf_router_if = self._interfaces[self._rpf_link].get_interface()
            old_if = self._interfaces.pop(self._rpf_link)

            self._create_root_if(self._rpf_link, rpf_router_if)

            old_if.is_now_root()
            old_if.delete()

            if self.is_in_group():
                self._up_if.send_join()

        if link_ch and node_ch:
            pass

        for interface in self._interfaces.values():
            interface.set_cost(self._unicastd.cost_to(self.get_source()))

    def nbr_event(self, link, node, event):
        '''
        @type link: Link
        @type node: Node
        @type event: NeighborEvent
        '''
        if NeighborEvent.timedOut == event:
            self._interfaces[link].nbr_died(node)

        elif NeighborEvent.genIdChanged == event:
            self._interfaces[link].nbr_connected()

        elif NeighborEvent.newNbr == event:
            self._interfaces[link].nbr_connected()

        else:
            assert False

    def is_in_group(self):
        if self.get_has_members():
            return True

        for interface in self._interfaces.values():
            if interface.is_forwarding():
                return True

        return False

    def evaluate_ingroup(self):
        is_ig = self.is_in_group()

        if self._was_in_group != is_ig:
            if is_ig:
                self.rprint('transitoned to IG')
                self._up_if.send_join()
            else:
                self.rprint('transitoned to OG')
                self._up_if.send_prune()

            self._was_in_group = is_ig

    def is_originater(self):
        return self._rpf_node == self.get_source()

    def delete(self):
        for interface in self._interfaces.values():
            interface.delete()

        self._liveliness_timer.stop()

        self.rprint('Tree deleted')
        Convergence.mark_change()

    def rprint(self, msg, *entrys):
        self._rprint(msg, '({}, {})'.format(self.get_tree_id()[0],
                                            self.get_tree_id()[1]), *entrys)

    def get_tree_id(self):
        return self._tree_id

    def get_source(self):
        return self._tree_id[0]

    def get_group(self):
        return self._tree_id[1]

    def get_node(self):
        '''
        @rtype: Node
        '''
        return self._node

    def get_has_members(self):
        return self._has_members

    def set_has_members(self, value):
        assert isinstance(value, bool)

        self._has_members = value
        self.evaluate_ingroup()

    def _create_root_if(self, link, router_interface):
        #        assert self._up_if is None
        assert link not in self._interfaces

        self._interfaces[link] = SFRMRootInterface(
            self.rprint, router_interface,
            self.get_node(),
            self.get_tree_id(),
            self._unicastd.cost_to(self.get_source()), self.evaluate_ingroup,
            self.is_originater())

        self._up_if = self._interfaces[link]

    def _create_non_root_if(self, link, router_interface):
        assert link not in self._interfaces

        nrif = SFRMNonRootInterface(self.rprint, router_interface,
                                    self.get_node(),
                                    self.get_tree_id(),
                                    self._unicastd.cost_to(self.get_source()),
                                    self.evaluate_ingroup)

        self._interfaces[link] = nrif

        nrif._dipt.start()
        nrif.send_prune()
