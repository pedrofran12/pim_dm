import struct
import socket
from Packet.PacketPimEncodedGroupAddress import PacketPimEncodedGroupAddress
from Packet.PacketPimEncodedSourceAddress import PacketPimEncodedSourceAddress

'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Multicast Group Address 1 (Encoded Group Format)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Number of Joined Sources    |   Number of Pruned Sources    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Joined Source Address 1 (Encoded Source Format)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               .                               |
|                               .                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Joined Source Address n (Encoded Source Format)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Pruned Source Address 1 (Encoded Source Format)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               .                               |
|                               .                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Pruned Source Address n (Encoded Source Format)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''


class PacketPimJoinPruneMulticastGroup:
    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP = "! %ss HH"
    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_WITHOUT_GROUP_ADDRESS = "! HH"

    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_v4_LEN_ = struct.calcsize(
        PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP % PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN)
    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_v6_LEN_ = struct.calcsize(
        PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP % PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN_IPv6)
    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_WITHOUT_GROUP_ADDRESS_LEN = struct.calcsize(
        PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_WITHOUT_GROUP_ADDRESS)

    PIM_HDR_JOINED_PRUNED_SOURCE = "! %ss"
    PIM_HDR_JOINED_PRUNED_SOURCE_v4_LEN = PacketPimEncodedSourceAddress.PIM_ENCODED_SOURCE_ADDRESS_HDR_LEN
    PIM_HDR_JOINED_PRUNED_SOURCE_v6_LEN = PacketPimEncodedSourceAddress.PIM_ENCODED_SOURCE_ADDRESS_HDR_LEN_IPV6

    def __init__(self, multicast_group, joined_src_addresses: list, pruned_src_addresses: list):
        if type(multicast_group) not in (str, bytes):
            raise Exception
        elif type(multicast_group) is bytes:
            self.multicast_group = socket.inet_ntoa(self.multicast_group)

        if type(joined_src_addresses) is not list:
            raise Exception
        if type(pruned_src_addresses) is not list:
            raise Exception

        self.multicast_group = multicast_group
        self.joined_src_addresses = joined_src_addresses
        self.pruned_src_addresses = pruned_src_addresses

    def bytes(self) -> bytes:
        multicast_group_address = PacketPimEncodedGroupAddress(self.multicast_group).bytes()
        msg = multicast_group_address + struct.pack(self.PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_WITHOUT_GROUP_ADDRESS,
                                                    len(self.joined_src_addresses), len(self.pruned_src_addresses))

        for joined_src_address in self.joined_src_addresses:
            joined_src_address_bytes = PacketPimEncodedSourceAddress(joined_src_address).bytes()
            msg += joined_src_address_bytes

        for pruned_src_address in self.pruned_src_addresses:
            pruned_src_address_bytes = PacketPimEncodedSourceAddress(pruned_src_address).bytes()
            msg += pruned_src_address_bytes
        return msg
