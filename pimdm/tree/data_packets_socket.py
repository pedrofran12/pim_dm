import struct
import socket
import ipaddress
from ctypes import create_string_buffer, addressof
from pcap_wrapper import bpf

SO_ATTACH_FILTER = 26
ETH_P_IP = 0x0800    # Internet Protocol packet
ETH_P_IPV6 = 0x86DD  # IPv6 over bluebook

SO_RCVBUFFORCE = 33

def get_s_g_bpf_filter_code(source, group, interface_name):
    ip_source_version = ipaddress.ip_address(source).version
    ip_group_version = ipaddress.ip_address(group).version
    if ip_source_version == ip_group_version == 4:
        # bpf_filter_str = "(udp or icmp) and host %s and dst %s" % (source, group)
        bpf_filter_str = "(ip proto not 2) and host %s and dst %s" % (source, group)
        protocol = ETH_P_IP
    elif ip_source_version == ip_group_version == 6:
        # TODO: allow ICMPv6 echo request/echo response to be considered multicast packets
        bpf_filter_str = "(ip6 proto not 58) and host %s and dst %s" % (source, group)
        protocol = ETH_P_IPV6
    else:
        raise Exception("Unknown IP family")

    num, bpf_filter = bpf(bpf_filter_str.encode()).compiled_filter()
    print(num)

    # defined in linux/filter.h.
    b = create_string_buffer(bpf_filter)
    mem_addr_of_filters = addressof(b)
    fprog = struct.pack('HL', num, mem_addr_of_filters)


    # Create listening socket with filters
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, protocol)
    s.setsockopt(socket.SOL_SOCKET, SO_ATTACH_FILTER, fprog)
    # todo pequeno ajuste (tamanho de buffer pequeno para o caso de trafego em rajadas):
    #s.setsockopt(socket.SOL_SOCKET, SO_RCVBUFFORCE, 1)
    s.bind((interface_name, protocol))

    return s
