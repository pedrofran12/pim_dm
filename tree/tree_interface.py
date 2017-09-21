'''
Created on Jul 16, 2015

@author: alex
'''
from abc import ABCMeta, abstractmethod
import Main
from threading import Lock, RLock
import traceback

#from convergence import Convergence
#from sfmr.messages.prune import SFMRPruneMsg
#from .router_interface import SFMRInterface


class SFRMTreeInterface(metaclass=ABCMeta):
    def __init__(self, kernel_entry, interface_id):
        '''
        @type interface: SFMRInterface
        @type node: Node
        '''
        #assert isinstance(interface, SFMRInterface)

        self._kernel_entry = kernel_entry
        self._interface_id = interface_id
        #self._interface = interface
        #self._node = node
        #self._tree_id = tree_id
        #self._cost = cost
        #self._evaluate_ig = evaluate_ig_cb

        try:
            interface_name = Main.kernel.vif_index_to_name_dic[interface_id]
            igmp_interface = Main.igmp_interfaces[interface_name]  # type: InterfaceIGMP
            group_state = igmp_interface.interface_state.get_group_state(kernel_entry.group_ip)
            self._igmp_has_members = group_state.add_multicast_routing_entry(self)
        except:
            #traceback.print_exc()
            self._igmp_has_members = False

        self._igmp_lock = RLock()

        #self.rprint('new ' + self.__class__.__name__)

    def recv_data_msg(self, msg, sender):
        pass

    @abstractmethod
    def recv_assert_msg(self, msg, sender):
        pass

    def recv_reset_msg(self, msg, sender):
        pass

    def recv_prune_msg(self, msg, sender, in_group):
        pass

    def recv_join_msg(self, msg, sender, in_group):
        pass

    def forward_state_reset_msg(self, msg):
        #self._interface.send_mcast(msg)
        # todo
        raise NotImplemented

    def send_prune(self):
        try:
            from Packet.Packet import Packet
            from Packet.PacketPimHeader import PacketPimHeader
            from Packet.PacketPimJoinPrune import PacketPimJoinPrune
            from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup

            (source, group) = self.get_tree_id()
            # todo help ip of ph
            ph = PacketPimJoinPrune("123.123.123.123", 210)
            ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, pruned_src_addresses=[source]))
            pckt = Packet(payload=PacketPimHeader(ph))

            self.get_interface().send(pckt.bytes())
            print('sent prune msg')
        except:
            return

    @abstractmethod
    def is_forwarding(self):
        pass

    def nbr_died(self, node):
        pass

    def nbr_connected(self):
        pass

    @abstractmethod
    def is_now_root(self):
        pass

    @abstractmethod
    def delete(self):
        print('Tree Interface deleted')

    def evaluate_ingroup(self):
        self._kernel_entry.evaluate_ingroup()

    def notify_igmp(self, has_members: bool):
        with self.get_state_lock():
            with self._igmp_lock:
                if has_members != self._igmp_has_members:
                    self._igmp_has_members = has_members
                    self.change_tree()
                    self.evaluate_ingroup()


    def igmp_has_members(self):
        with self._igmp_lock:
            return self._igmp_has_members

    '''
    def rprint(self, msg, *entrys):
        self._rprint(msg,
                     self._interface.get_link(),
                     *entrys)
    '''
    def rprint(self, msg, *entrys):
        return

    def __str__(self):
        return '{}<{}>'.format(self.__class__, self._interface.get_link())

    def get_link(self):
        # todo
        return self._interface.get_link()

    def get_interface(self):
        kernel = Main.kernel
        interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        interface = Main.interfaces[interface_name]
        return interface

    def get_node(self):
        # todo: para ser substituido por get_ip
        return self.get_ip()

    def get_ip(self):
        #kernel = Main.kernel
        #interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        #import netifaces
        #netifaces.ifaddresses(interface_name)
        #ip = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']
        ip = self.get_interface().get_ip()
        return ip

    def get_tree_id(self):
        return (self._kernel_entry.source_ip, self._kernel_entry.group_ip)

    def get_cost(self):
        #return self._cost
        # todo
        return 10

    def set_cost(self, value):
        self._cost = value

    def change_tree(self):
        self._kernel_entry.change()

    def get_state_lock(self):
        return self._kernel_entry.CHANGE_STATE_LOCK
