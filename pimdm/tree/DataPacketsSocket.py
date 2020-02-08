import subprocess
import struct
import socket
from ctypes import create_string_buffer, addressof

SO_ATTACH_FILTER = 26
ETH_P_IP = 0x0800  # Internet Protocol packet
SO_RCVBUFFORCE = 33

def get_s_g_bpf_filter_code(source, group, interface_name):
    #cmd = "tcpdump -ddd \"(udp or icmp) and host %s and dst %s\"" % (source, group)
    cmd = "tcpdump -ddd \"(ip proto not 2) and host %s and dst %s\"" % (source, group)
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    bpf_filter = b''

    tmp = result.stdout.read().splitlines()
    num = int(tmp[0])
    for line in tmp[1:]:
        print(line)
        bpf_filter += struct.pack("HBBI", *tuple(map(int, line.split(b' '))))

    print(num)

    # defined in linux/filter.h.
    b = create_string_buffer(bpf_filter)
    mem_addr_of_filters = addressof(b)
    fprog = struct.pack('HL', num, mem_addr_of_filters)


    # Create listening socket with filters
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, ETH_P_IP)
    s.setsockopt(socket.SOL_SOCKET, SO_ATTACH_FILTER, fprog)
    # todo pequeno ajuste (tamanho de buffer pequeno para o caso de trafego em rajadas):
    #s.setsockopt(socket.SOL_SOCKET, SO_RCVBUFFORCE, 1)
    s.bind((interface_name, ETH_P_IP))

    return s
