import Main
import socket
from tree.root_interface import SFRMRootInterface
from tree.non_root_interface import SFRMNonRootInterface
from threading import Timer, Lock
import UnicastRouting

class KernelEntry:
    TREE_TIMEOUT = 180


    def __init__(self, source_ip: str, group_ip: str, inbound_interface_index: int):
        self.source_ip = source_ip
        self.group_ip = group_ip

        # ip of neighbor of the rpf
        self._rpf_node = None

        # (S,G) starts IG state
        self._was_in_group = True

        # todo
        self._rpf_is_origin = False

        # decide inbound interface based on rpf check
        self.inbound_interface_index = Main.kernel.vif_dic[self.check_rpf()]


        Main.kernel.flood(source_ip, group_ip, self.inbound_interface_index)


        self.interface_state = {}  # type: Dict[int, SFRMTreeInterface]
        #for i in range(Main.kernel.MAXVIFS):
        for i in Main.kernel.vif_index_to_name_dic.keys():
            try:
                if i == self.inbound_interface_index:
                    self.interface_state[i] = SFRMRootInterface(self, i, False)
                else:
                    self.interface_state[i] = SFRMNonRootInterface(self, i)
            except:
                continue

        self._multicast_change = Lock()
        self._lock_test2 = Lock()

        self.CHANGE_STATE_LOCK = Lock()

        print('Tree created')
        self._liveliness_timer = None
        if self.is_originater():
            self.set_liveliness_timer()
            print('set SAT')

        #self._lock = threading.RLock()


    def get_inbound_interface_index(self):
        return self.inbound_interface_index

    def get_outbound_interfaces_indexes(self):
        outbound_indexes = [0]*Main.kernel.MAXVIFS
        for (index, state) in self.interface_state.items():
            outbound_indexes[index] = state.is_forwarding()
        return outbound_indexes

    def check_rpf(self):
        return UnicastRouting.check_rpf(self.source_ip)

    def recv_data_msg(self, index):
        if self.is_originater():
            self.clear_liveliness_timer()

        self.interface_state[index].recv_data_msg(None, None)

    def recv_assert_msg(self, index, packet):
        print("recv assert msg")
        self.interface_state[index].recv_assert_msg(packet, None)

    def recv_reset_msg(self, msg, sender):
        # todo
        return

    def recv_prune_msg(self, index, packet):
        print("recv prune msg")
        self.interface_state[index].recv_prune_msg(packet, None, self.is_in_group())

    def recv_join_msg(self, index, packet):
        print("recv join msg")
        self.interface_state[index].recv_join_msg(packet, None, self.is_in_group())

    def recv_state_reset_msg(self, msg, sender):
        # todo
        return

    def set_liveliness_timer(self):
        self.clear_liveliness_timer()
        timer = Timer(self.TREE_TIMEOUT, self.___liveliness_timer_expired)
        timer.start()
        self._liveliness_timer = timer

    def clear_liveliness_timer(self):
        if self._liveliness_timer is not None:
            self._liveliness_timer.cancel()

    def ___liveliness_timer_expired(self):
        #todo
        return

    def network_update(self, change, args):
        #todo
        return

    def update(self, caller, arg):
        #todo
        return


    def nbr_event(self, link, node, event):
        # todo
        return

    def nbr_died(self, index, neighbor_ip):
        # todo
        self.interface_state[index].nbr_died(neighbor_ip)

    def is_in_group(self):
        # todo
        #if self.get_has_members():
        #if True:
        #    return True

        for interface in self.interface_state.values():
            if interface.is_forwarding():
                return True
        return False


    def evaluate_ingroup(self):
        with self._lock_test2:
            is_ig = self.is_in_group()

            if self._was_in_group != is_ig:
                if is_ig:
                    print('transitoned to IG')
                    #self._up_if.send_join()
                    self.interface_state[self.inbound_interface_index].send_join()
                else:
                    print('transitoned to OG')
                    #self._up_if.send_prune()
                    self.interface_state[self.inbound_interface_index].send_prune()

                self._was_in_group = is_ig

    def is_originater(self):
        # todo
        #return self._rpf_node == self.get_source()
        return False

    def get_source(self):
        return self.source_ip

    def get_group(self):
        return self.group_ip

    def change(self):
        # todo: changes on unicast routing or multicast routing...
        with self._multicast_change:
            Main.kernel.set_multicast_route(self)

    def delete(self):
        for state in self.interface_state.values():
            state.delete()

        self.clear_liveliness_timer()
        Main.kernel.remove_multicast_route(self)
