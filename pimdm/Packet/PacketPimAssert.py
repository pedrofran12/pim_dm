import struct
import socket
from .PacketPimEncodedGroupAddress import PacketPimEncodedGroupAddress
from .PacketPimEncodedUnicastAddress import PacketPimEncodedUnicastAddress
from pimdm.tree.globals import ASSERT_CANCEL_METRIC
'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|PIM Ver| Type  |   Reserved    |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Multicast Group Address (Encoded Group Format)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|             Source Address (Encoded Unicast Format)           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|R|                     Metric Preference                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Metric                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketPimAssert:
    PIM_TYPE = 5

    PIM_HDR_ASSERT = "! %ss %ss LL"
    PIM_HDR_ASSERT_WITHOUT_ADDRESS = "! LL"
    PIM_HDR_ASSERT_v4 = PIM_HDR_ASSERT % (PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN, PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN)
    PIM_HDR_ASSERT_v6 = PIM_HDR_ASSERT % (PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN_IPv6, PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN_IPV6)

    PIM_HDR_ASSERT_WITHOUT_ADDRESS_LEN = struct.calcsize(PIM_HDR_ASSERT_WITHOUT_ADDRESS)
    PIM_HDR_ASSERT_v4_LEN = struct.calcsize(PIM_HDR_ASSERT_v4)
    PIM_HDR_ASSERT_v6_LEN = struct.calcsize(PIM_HDR_ASSERT_v6)

    def __init__(self, multicast_group_address: str or bytes, source_address: str or bytes, metric_preference: int or float, metric: int or float):
        if type(multicast_group_address) is bytes:
            multicast_group_address = socket.inet_ntoa(multicast_group_address)
        if type(source_address) is bytes:
            source_address = socket.inet_ntoa(source_address)
        if metric_preference > 0x7FFFFFFF:
            metric_preference = 0x7FFFFFFF
        if metric > ASSERT_CANCEL_METRIC:
            metric = ASSERT_CANCEL_METRIC
        self.multicast_group_address = multicast_group_address
        self.source_address = source_address
        self.metric_preference = metric_preference
        self.metric = metric

    def bytes(self) -> bytes:
        multicast_group_address = PacketPimEncodedGroupAddress(self.multicast_group_address).bytes()
        source_address = PacketPimEncodedUnicastAddress(self.source_address).bytes()

        msg = multicast_group_address + source_address + struct.pack(PacketPimAssert.PIM_HDR_ASSERT_WITHOUT_ADDRESS,
                                                                     0x7FFFFFFF & self.metric_preference,
                                                                     self.metric)
        return msg

    def __len__(self):
        return len(self.bytes())

    @staticmethod
    def parse_bytes(data: bytes):
        multicast_group_addr_obj = PacketPimEncodedGroupAddress.parse_bytes(data)
        multicast_group_addr_len = len(multicast_group_addr_obj)
        data = data[multicast_group_addr_len:]

        source_addr_obj = PacketPimEncodedUnicastAddress.parse_bytes(data)
        source_addr_len = len(source_addr_obj)
        data = data[source_addr_len:]

        (metric_preference, metric) = struct.unpack(PacketPimAssert.PIM_HDR_ASSERT_WITHOUT_ADDRESS, data[:PacketPimAssert.PIM_HDR_ASSERT_WITHOUT_ADDRESS_LEN])
        pim_payload = PacketPimAssert(multicast_group_addr_obj.group_address, source_addr_obj.unicast_address, 0x7FFFFFFF & metric_preference, metric)

        return pim_payload
