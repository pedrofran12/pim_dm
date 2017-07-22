import struct


class PacketPimJoinPrune:
    PIM_TYPE = 3
    PIM_HDR_JOIN_PRUNE = "! 4s BBH "
    PIM_HDR_JOIN_PRUNE_LEN = struct.calcsize(PIM_HDR_JOIN_PRUNE)

    def __init__(self, upstream_neighbor_address, hold_time):
        self.groups = []
        self.upstream_neighbor_address = upstream_neighbor_address
        self.hold_time = hold_time

    def add_multicast_group(self, group):
        # TODO verificar se grupo ja esta na msg
        self.groups.append(group)

    def bytes(self) -> bytes:
        # TODO esta a converter upstream neighbor (considera que recebe int) para bytes
        msg = struct.pack(PacketPimJoinPrune.PIM_HDR_JOIN_PRUNE, self.upstream_neighbor_address.to_bytes(4, byteorder='big'), 0, len(self.groups), self.hold_time)

        for multicast_group in self.groups:
            msg += multicast_group.bytes()

        return msg
