import struct
import socket
from .PacketPimEncodedUnicastAddress import PacketPimEncodedUnicastAddress
from .PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Upstream Neighbor Address (Encoded Unicast Format)     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Reserved    |  Num Groups   |          Hold Time            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketPimJoinPrune:
    PIM_TYPE = 3

    PIM_HDR_JOIN_PRUNE = "! %ss BBH"
    PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS = "! BBH"
    PIM_HDR_JOIN_PRUNE_v4 = PIM_HDR_JOIN_PRUNE % PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN
    PIM_HDR_JOIN_PRUNE_v6 = PIM_HDR_JOIN_PRUNE % PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN_IPV6

    PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS_LEN = struct.calcsize(PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS)
    PIM_HDR_JOIN_PRUNE_v4_LEN = struct.calcsize(PIM_HDR_JOIN_PRUNE_v4)
    PIM_HDR_JOIN_PRUNE_v6_LEN = struct.calcsize(PIM_HDR_JOIN_PRUNE_v6)

    def __init__(self, upstream_neighbor_address, hold_time):
        if type(upstream_neighbor_address) not in (str, bytes):
            raise Exception
        if type(upstream_neighbor_address) is bytes:
            upstream_neighbor_address = socket.inet_ntoa(upstream_neighbor_address)
        self.groups = []
        self.upstream_neighbor_address = upstream_neighbor_address
        self.hold_time = hold_time

    def add_multicast_group(self, group: PacketPimJoinPruneMulticastGroup):
        # TODO verificar se grupo ja esta na msg
        self.groups.append(group)

    def bytes(self) -> bytes:
        upstream_neighbor_address = PacketPimEncodedUnicastAddress(self.upstream_neighbor_address).bytes()
        msg = upstream_neighbor_address + struct.pack(PacketPimJoinPrune.PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS, 0,
                                                      len(self.groups), self.hold_time)

        for multicast_group in self.groups:
            msg += multicast_group.bytes()

        return msg

    def __len__(self):
        return len(self.bytes())

    @classmethod
    def parse_bytes(cls, data: bytes):
        upstream_neighbor_addr_obj = PacketPimEncodedUnicastAddress.parse_bytes(data)
        upstream_neighbor_addr_len = len(upstream_neighbor_addr_obj)
        data = data[upstream_neighbor_addr_len:]

        (_, num_groups, hold_time) = struct.unpack(PacketPimJoinPrune.PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS,
                                                   data[:PacketPimJoinPrune.PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS_LEN])
        data = data[PacketPimJoinPrune.PIM_HDR_JOIN_PRUNE_WITHOUT_ADDRESS_LEN:]
        pim_payload = cls(upstream_neighbor_addr_obj.unicast_address, hold_time)

        for i in range(0, num_groups):
            group = PacketPimJoinPruneMulticastGroup.parse_bytes(data)
            group_len = len(group)

            pim_payload.add_multicast_group(group)
            data = data[group_len:]

        return pim_payload
