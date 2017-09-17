import Main
import socket
import struct
import netifaces
import threading
from tree.root_interface import SFRMRootInterface
from tree.non_root_interface import SFRMNonRootInterface
from threading import Timer

class KernelEntry:
    TREE_TIMEOUT = 180


    def __init__(self, source_ip: str, group_ip: str, inbound_interface_index: int):
        self.source_ip = source_ip
        self.group_ip = group_ip

        # ip of neighbor of the rpf
        self._rpf_node = None

        self._has_members = True # todo check via igmp
        self._was_in_group = True
        self._rpf_is_origin = False

        self._liveliness_timer = None


        # decide inbound interface based on rpf check
        self.inbound_interface_index = Main.kernel.vif_dic[self.check_rpf()]

        #Main.kernel.flood(ip_src=source_ip, ip_dst=group_ip, iif=self.inbound_interface_index)
        #import time
        #time.sleep(5)

        self.interface_state = {}  # type: Dict[int, SFRMTreeInterface]
        for i in range(Main.kernel.MAXVIFS):
            if i == self.inbound_interface_index:
                self.interface_state[i] = SFRMRootInterface(self, i, False)
            else:
                self.interface_state[i] = SFRMNonRootInterface(self, i)

        print('Tree created')
        self.evaluate_ingroup()

        if self.is_originater():
            self.set_liveliness_timer()
            print('set SAT')

        self._lock = threading.RLock()


    def get_inbound_interface_index(self):
        return self.inbound_interface_index

    def get_outbound_interfaces_indexes(self):
        outbound_indexes = [0]*Main.kernel.MAXVIFS
        for (index, state) in self.interface_state.items():
            outbound_indexes[index] = state.is_forwarding()
        return outbound_indexes

    def check_rpf(self):
        from pyroute2 import IPRoute
        # from utils import if_indextoname

        ipr = IPRoute()
        # obter index da interface
        # rpf_interface_index = ipr.get_routes(family=socket.AF_INET, dst=ip)[0]['attrs'][2][1]
        # interface_name = if_indextoname(rpf_interface_index)
        # return interface_name

        # obter ip da interface de saida
        rpf_interface_source = ipr.get_routes(family=socket.AF_INET, dst=self.source_ip)[0]['attrs'][3][1]
        return rpf_interface_source

    def recv_data_msg(self, index):
        if self.is_originater():
            self.clear_liveliness_timer()

        self.interface_state[index].recv_data_msg()

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

    def is_in_group(self):
        # todo
        #if self.get_has_members():
        if True:
            return True

        for interface in self.interface_state.values():
            if interface.is_forwarding():
                return True

        return False

    def evaluate_ingroup(self):
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

    def get_has_members(self):
        #return self._has_members
        return True

    def set_has_members(self, value):
        assert isinstance(value, bool)

        self._has_members = value
        self.evaluate_ingroup()

    def change(self):
        # todo: changes on unicast routing or multicast routing...

        Main.kernel.set_multicast_route(self)

    def delete(self):
        for state in self.interface_state.values():
            state.delete()

        self.clear_liveliness_timer()
        Main.kernel.remove_multicast_route(self)
