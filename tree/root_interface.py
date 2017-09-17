'''
Created on Jul 16, 2015

@author: alex
'''
#from des.addr import Addr

#from .messages.assert_msg import SFMRAssertMsg
#from .messages.join import SFMRJoinMsg
from .tree_interface import SFRMTreeInterface


class SFRMRootInterface(SFRMTreeInterface):
    def __init__(
            self, kernel_entry, interface_id, is_originater: bool):
        '''
        interface,
        node,
        tree_id,
        cost,
        evaluate_ig_cb,
        is_originater: bool, ):
        '''
        SFRMTreeInterface.__init__(self, kernel_entry, interface_id, None)
        self._is_originater = is_originater

    #Override
    #def recv_assert_msg(self, msg: SFMRAssertMsg, sender: Addr):
    def recv_assert_msg(self, msg, sender):
        pass

    #Override
    def recv_prune_msg(self, msg, sender, in_group):
        super().recv_prune_msg(msg, sender, in_group)

        if in_group:
            print("I WILL SEND JOIN")
            self.send_join()
            print("I SENT JOIN")


    def forward_data_msg(self, msg):
        pass

    def send_join(self):
        # Originaters dont need to send prunes or joins
        if self._is_originater:
            return
        print("I WILL SEND JOIN")

        #msg = SFMRJoinMsg(self.get_tree_id())
        from Packet.Packet import Packet
        from Packet.PacketPimHeader import PacketPimHeader
        from Packet.PacketPimJoinPrune import PacketPimJoinPrune
        from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup

        (source, group) = self.get_tree_id()
        # todo help ip of upstream neighbor
        ph = PacketPimJoinPrune("123.123.123.123", 210)
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup(group, joined_src_addresses=[source]))
        pckt = Packet(payload=PacketPimHeader(ph))

        self.get_interface().send(pckt.bytes())
        print('sent join msg')


    #Override
    def is_forwarding(self):
        return False

    #Override
    def is_now_root(self):
        assert False

    #Override
    def delete(self):
        super().delete()
