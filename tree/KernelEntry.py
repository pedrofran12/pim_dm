import Main
import socket

from tree.originator import OriginatorState
from tree.tree_if_upstream import TreeInterfaceUpstream
from tree.tree_if_downstream import TreeInterfaceDownstream
from .tree_interface import TreeInterface
from threading import Timer, Lock, RLock
import UnicastRouting

class KernelEntry:
    TREE_TIMEOUT = 180


    def __init__(self, source_ip: str, group_ip: str, inbound_interface_index: int):
        self.source_ip = source_ip
        self.group_ip = group_ip

        # ip of neighbor of the rpf
        self._rpf_node = None

        # (S,G) starts IG state
        self._was_olist_null = None

        # todo
        #self._rpf_is_origin = False
        self._originator_state = OriginatorState.NotOriginator

        # decide inbound interface based on rpf check
        self.inbound_interface_index = Main.kernel.vif_dic[self.check_rpf()]


        Main.kernel.flood(source_ip, group_ip, self.inbound_interface_index)


        self.interface_state = {}  # type: Dict[int, TreeInterface]
        for i in Main.kernel.vif_index_to_name_dic.keys():
            try:
                if i == self.inbound_interface_index:
                    self.interface_state[i] = TreeInterfaceUpstream(self, i, False)
                else:
                    self.interface_state[i] = TreeInterfaceDownstream(self, i)
            except:
                import traceback
                print(traceback.print_exc())
                continue

        self._multicast_change = Lock()
        self._lock_test2 = RLock()
        self.CHANGE_STATE_LOCK = RLock()
        #self._was_olist_null = self.is_olist_null()

        print('Tree created')
        #self._liveliness_timer = None
        #if self.is_originater():
        #    self.set_liveliness_timer()
        #    print('set SAT')

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


    #################################
    # Receive (S,G) packet
    #################################
    def recv_data_msg(self, index):
        print("recv data")
        self.interface_state[index].recv_data_msg()

    def recv_assert_msg(self, index, packet):
        print("recv assert")
        self.interface_state[index].recv_assert_msg()

    def recv_prune_msg(self, index, packet):
        print("recv prune msg")
        self.interface_state[index].recv_prune_msg()

    def recv_join_msg(self, index, packet):
        print("recv join msg")
        print("type: ")
        self.interface_state[index].recv_join_msg()

    def recv_graft_msg(self, index, packet):
        print("recv graft msg")
        self.interface_state[index].recv_graft_msg()

    def recv_graft_ack_msg(self, index, packet):
        print("recv graft ack msg")
        self.interface_state[index].recv_graft_ack_msg()

    def recv_state_refresh_msg(self, index, packet):
        print("recv state refresh msg")
        prune_indicator = 1
        self.interface_state[index].recv_state_refresh_msg(prune_indicator)

    def network_update(self, change, args):
        #todo
        return





    def update(self, caller, arg):
        #todo
        return


    def nbr_event(self, link, node, event):
        # todo
        return

    def is_olist_null(self):
        for interface in self.interface_state.values():
            if interface.is_forwarding():
                return False
        return True

    def evaluate_olist_change(self):
        with self._lock_test2:
            is_olist_null = self.is_olist_null()

            if self._was_olist_null != is_olist_null:
                if is_olist_null:
                    self.interface_state[self.inbound_interface_index].olist_is_null()
                else:
                    self.interface_state[self.inbound_interface_index].olist_is_not_null()

                self._was_olist_null = is_olist_null

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

        Main.kernel.remove_multicast_route(self)
