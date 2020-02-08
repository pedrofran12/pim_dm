import struct
import socket
from .PacketPimEncodedUnicastAddress import PacketPimEncodedUnicastAddress
from .PacketPimEncodedGroupAddress import PacketPimEncodedGroupAddress
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
|           Originator Address (Encoded Unicast Format)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|R|                     Metric Preference                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Metric                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Masklen    |    TTL        |P|N|O|Reserved |   Interval    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
class PacketPimStateRefresh:
    PIM_TYPE = 9

    PIM_HDR_STATE_REFRESH = "! %ss %ss %ss I I BBBB"
    PIM_HDR_STATE_REFRESH_WITHOUT_ADDRESSES = "! I I BBBB"
    PIM_HDR_STATE_REFRESH_v4 = PIM_HDR_STATE_REFRESH % (PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN, PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN, PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN)
    PIM_HDR_STATE_REFRESH_v6 = PIM_HDR_STATE_REFRESH % (PacketPimEncodedGroupAddress.PIM_ENCODED_GROUP_ADDRESS_HDR_LEN_IPv6, PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN_IPV6, PacketPimEncodedUnicastAddress.PIM_ENCODED_UNICAST_ADDRESS_HDR_LEN_IPV6)

    PIM_HDR_STATE_REFRESH_WITHOUT_ADDRESSES_LEN = struct.calcsize(PIM_HDR_STATE_REFRESH_WITHOUT_ADDRESSES)
    PIM_HDR_STATE_REFRESH_v4_LEN = struct.calcsize(PIM_HDR_STATE_REFRESH_v4)
    PIM_HDR_STATE_REFRESH_v6_LEN = struct.calcsize(PIM_HDR_STATE_REFRESH_v6)

    def __init__(self, multicast_group_adress: str or bytes, source_address: str or bytes, originator_adress: str or bytes,
                 metric_preference: int, metric: int, mask_len: int, ttl: int, prune_indicator_flag: bool,
                 prune_now_flag: bool, assert_override_flag: bool, interval: int):

        if type(multicast_group_adress) is bytes:
            multicast_group_adress = socket.inet_ntoa(multicast_group_adress)
        if type(source_address) is bytes:
            source_address = socket.inet_ntoa(source_address)
        if type(originator_adress) is bytes:
            originator_adress = socket.inet_ntoa(originator_adress)

        self.multicast_group_adress = multicast_group_adress
        self.source_address = source_address
        self.originator_adress = originator_adress
        self.metric_preference = metric_preference
        self.metric = metric
        self.mask_len = mask_len
        self.ttl = ttl
        self.prune_indicator_flag = prune_indicator_flag
        self.prune_now_flag = prune_now_flag
        self.assert_override_flag = assert_override_flag
        self.interval = interval

    def bytes(self) -> bytes:
        multicast_group_adress = PacketPimEncodedGroupAddress(self.multicast_group_adress).bytes()
        source_address = PacketPimEncodedUnicastAddress(self.source_address).bytes()
        originator_adress = PacketPimEncodedUnicastAddress(self.originator_adress).bytes()
        prune_and_assert_flags = (self.prune_indicator_flag << 7) | (self.prune_now_flag << 6) | (self.assert_override_flag << 5)

        msg = multicast_group_adress + source_address + originator_adress + \
              struct.pack(self.PIM_HDR_STATE_REFRESH_WITHOUT_ADDRESSES, 0x7FFFFFFF & self.metric_preference,
                          self.metric, self.mask_len, self.ttl, prune_and_assert_flags, self.interval)

        return msg

    def __len__(self):
        return len(self.bytes())

    @staticmethod
    def parse_bytes(data: bytes):
        multicast_group_adress_obj = PacketPimEncodedGroupAddress.parse_bytes(data)
        multicast_group_adress_len = len(multicast_group_adress_obj)
        data = data[multicast_group_adress_len:]

        source_address_obj = PacketPimEncodedUnicastAddress.parse_bytes(data)
        source_address_len = len(source_address_obj)
        data = data[source_address_len:]

        originator_address_obj = PacketPimEncodedUnicastAddress.parse_bytes(data)
        originator_address_len = len(originator_address_obj)
        data = data[originator_address_len:]

        (metric_preference, metric, mask_len, ttl, reserved_and_prune_and_assert_flags, interval) = struct.unpack(PacketPimStateRefresh.PIM_HDR_STATE_REFRESH_WITHOUT_ADDRESSES, data[:PacketPimStateRefresh.PIM_HDR_STATE_REFRESH_WITHOUT_ADDRESSES_LEN])
        metric_preference = 0x7FFFFFFF & metric_preference
        prune_indicator_flag = (0x80 & reserved_and_prune_and_assert_flags) >> 7
        prune_now_flag = (0x40 & reserved_and_prune_and_assert_flags) >> 6
        assert_override_flag = (0x20 & reserved_and_prune_and_assert_flags) >> 5

        pim_payload = PacketPimStateRefresh(multicast_group_adress_obj.group_address, source_address_obj.unicast_address,
                                            originator_address_obj.unicast_address, metric_preference, metric, mask_len,
                                            ttl, prune_indicator_flag, prune_now_flag, assert_override_flag, interval)

        return pim_payload
