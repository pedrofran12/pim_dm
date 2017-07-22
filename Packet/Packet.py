from Packet.PacketIpHeader import PacketIpHeader
from Packet.PacketPimHeader import PacketPimHeader


class Packet:
    # ter ip header
    # pim header
    # pim options
    def __init__(self, ip_header: PacketIpHeader = None, pim_header: PacketPimHeader = None):
        self.ip_header = ip_header
        self.pim_header = pim_header

    # maybe remover
    '''def add_option(self, option: PacketPimOption):
        self.pim_header.add_option(option)
    '''
    def bytes(self):
        return self.pim_header.bytes()
