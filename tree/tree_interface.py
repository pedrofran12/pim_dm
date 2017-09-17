'''
Created on Jul 16, 2015

@author: alex
'''
from abc import ABCMeta, abstractmethod
import Main
#from convergence import Convergence
#from sfmr.messages.prune import SFMRPruneMsg
#from .router_interface import SFMRInterface


class SFRMTreeInterface(metaclass=ABCMeta):
    def __init__(self, kernel_entry, interface_id, evaluate_ig_cb):
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
        self._evaluate_ig = evaluate_ig_cb

        #self.rprint('new ' + self.__class__.__name__)
        #Convergence.mark_change()

    def recv_data_msg(self, msg, sender):
        pass

    @abstractmethod
    def recv_assert_msg(self, msg, sender):
        pass

    def recv_reset_msg(self, msg, sender):
        pass

    def recv_prune_msg(self, msg, sender, in_group):
        print("SUPER PRUNE")
        pass

    def recv_join_msg(self, msg, sender, in_group):
        print("SUPER JOIN")
        pass

    @abstractmethod
    def forward_data_msg(self, msg):
        pass

    def forward_state_reset_msg(self, msg):
        self._interface.send_mcast(msg)

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
        # todo help self._evaluate_ig()
        return

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
        return self._interface.get_link()

    def get_interface(self):
        import Main
        kernel = Main.kernel
        interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        interface = Main.interfaces[interface_name]
        return interface

    def get_node(self):
        # todo: para ser substituido por get_ip
        return self.get_ip()

    def get_ip(self):
        import Main
        kernel = Main.kernel
        interface_name = kernel.vif_index_to_name_dic[self._interface_id]
        import netifaces
        netifaces.ifaddresses(interface_name)
        ip = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']
        return ip

    def get_tree_id(self):
        #return self._tree_id
        return (self._kernel_entry.source_ip, self._kernel_entry.group_ip)

    def get_cost(self):
        #return self._cost
        return 10

    def set_cost(self, value):
        self._cost = value

    def change_tree(self):
        self._kernel_entry.change()
