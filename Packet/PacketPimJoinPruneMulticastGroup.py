import struct


class PacketPimJoinPruneMulticastGroup:
    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP = "! 4s HH"
    PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP_LEN = struct.calcsize(PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP)

    PIM_HDR_JOINED_PRUNED_SOURCE = "! 4s"
    PIM_HDR_JOINED_PRUNED_SOURCE_LEN = struct.calcsize(PIM_HDR_JOINED_PRUNED_SOURCE)


    def __init__(self, multicast_group, joined_src_addresses, pruned_src_addresses):
        self.multicast_group = multicast_group
        self.joined_src_addresses = joined_src_addresses
        self.pruned_src_addresses = pruned_src_addresses

    def bytes(self) -> bytes:
        # TODO: verificar multicast_group
        msg = struct.pack(self.PIM_HDR_JOIN_PRUNE_MULTICAST_GROUP, self.multicast_group.to_bytes(4, byteorder='big'), len(self.joined_src_addresses), len(self.pruned_src_addresses))

        for joined_src_address in self.joined_src_addresses:
            msg += struct.pack(self.PIM_HDR_JOINED_PRUNED_SOURCE, joined_src_address.to_bytes(4, byteorder='big'))

        for pruned_src_address in self.pruned_src_addresses:
            msg += struct.pack(self.PIM_HDR_JOINED_PRUNED_SOURCE, pruned_src_address.to_bytes(4, byteorder='big'))
        # TODO: verificar pruned e joined addrss
        return msg
