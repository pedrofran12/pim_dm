import struct
import socket


class PacketIpHeader:
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version|
    +-+-+-+-+
    """
    IP_HDR = "! B"
    IP_HDR_LEN = struct.calcsize(IP_HDR)

    def __init__(self, ver, hdr_len):
        self.version = ver
        self.hdr_length = hdr_len

    def __len__(self):
        return self.hdr_length

    @staticmethod
    def parse_bytes(data: bytes):
        (verhlen, ) = struct.unpack(PacketIpHeader.IP_HDR, data[:PacketIpHeader.IP_HDR_LEN])
        ver = (verhlen & 0xF0) >> 4
        print("ver:", ver)
        return PACKET_HEADER.get(ver).parse_bytes(data)


class PacketIpv4Header(PacketIpHeader):
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version|  IHL  |Type of Service|          Total Length         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Identification        |Flags|      Fragment Offset    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |  Time to Live |    Protocol   |         Header Checksum       |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Source Address                          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Destination Address                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Options                    |    Padding    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    IP_HDR = "! BBH HH BBH 4s 4s"
    IP_HDR_LEN = struct.calcsize(IP_HDR)

    def __init__(self, ver, hdr_len, ttl, proto, ip_src, ip_dst):
        super().__init__(ver, hdr_len)
        self.ttl = ttl
        self.proto = proto
        self.ip_src = ip_src
        self.ip_dst = ip_dst

    def __len__(self):
        return self.hdr_length

    @staticmethod
    def parse_bytes(data: bytes):
        (verhlen, tos, iplen, ipid, frag, ttl, proto, cksum, src, dst) = \
            struct.unpack(PacketIpv4Header.IP_HDR, data[:PacketIpv4Header.IP_HDR_LEN])

        ver = (verhlen & 0xf0) >> 4
        hlen = (verhlen & 0x0f) * 4

        '''
        "VER": ver,
        "HLEN": hlen,
        "TOS": tos,
        "IPLEN": iplen,
        "IPID": ipid,
        "FRAG": frag,
        "TTL": ttl,
        "PROTO": proto,
        "CKSUM": cksum,
        "SRC": socket.inet_ntoa(src),
        "DST": socket.inet_ntoa(dst)
        '''
        src_ip = socket.inet_ntoa(src)
        dst_ip = socket.inet_ntoa(dst)
        return PacketIpv4Header(ver, hlen, ttl, proto, src_ip, dst_ip)


class PacketIpv6Header(PacketIpHeader):
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version| Traffic Class |           Flow Label                  |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Payload Length        |  Next Header  |   Hop Limit   |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +                                                               +
    |                                                               |
    +                         Source Address                        +
    |                                                               |
    +                                                               +
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +                                                               +
    |                                                               |
    +                      Destination Address                      +
    |                                                               |
    +                                                               +
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    IP6_HDR = "! I HBB 16s 16s"
    IP6_HDR_LEN = struct.calcsize(IP6_HDR)

    def __init__(self, ver, next_header, hop_limit, ip_src, ip_dst):
        # TODO: confirm hdr_length in case of multiple options/headers
        super().__init__(ver, PacketIpv6Header.IP6_HDR_LEN)
        self.next_header = next_header
        self.hop_limit = hop_limit
        self.ip_src = ip_src
        self.ip_dst = ip_dst

    def __len__(self):
        return PacketIpv6Header.IP6_HDR_LEN

    @staticmethod
    def parse_bytes(data: bytes):
        (ver_tc_fl, _, next_header, hop_limit, src, dst) = \
            struct.unpack(PacketIpv6Header.IP6_HDR, data[:PacketIpv6Header.IP6_HDR_LEN])

        ver = (ver_tc_fl & 0xf0000000) >> 28
        #tc = (ver_tc_fl & 0x0ff00000) >> 20
        #fl = (ver_tc_fl & 0x000fffff)
        '''
        "VER": ver,
        "TRAFFIC CLASS": tc,
        "FLOW LABEL": fl,
        "PAYLOAD LEN": payload_length,
        "NEXT HEADER": next_header,
        "HOP LIMIT": hop_limit,
        "SRC": socket.inet_atop(socket.AF_INET6, src),
        "DST": socket.inet_atop(socket.AF_INET6, dst)
        '''

        src_ip = socket.inet_ntop(socket.AF_INET6, src)
        dst_ip = socket.inet_ntop(socket.AF_INET6, dst)
        return PacketIpv6Header(ver, next_header, hop_limit, src_ip, dst_ip)


PACKET_HEADER = {
    4: PacketIpv4Header,
    6: PacketIpv6Header,
}
