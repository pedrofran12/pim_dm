import socket
import struct
import threading
import netifaces
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback
from ctypes import create_string_buffer, addressof
if not hasattr(socket, 'SO_BINDTODEVICE'):
    socket.SO_BINDTODEVICE = 25


class InterfaceIGMP(object):
    ETH_P_IP = 0x0800		# Internet Protocol packet

    FILTER_IGMP = [
        struct.pack('HBBI', 0x28, 0, 0, 0x0000000c),
        struct.pack('HBBI', 0x15, 0, 3, 0x00000800),
        struct.pack('HBBI', 0x30, 0, 0, 0x00000017),
        struct.pack('HBBI', 0x15, 0, 1, 0x00000002),
        struct.pack('HBBI', 0x6, 0, 0, 0x00040000),
        struct.pack('HBBI', 0x6, 0, 0, 0x00000000),
    ]

    SO_ATTACH_FILTER = 26

    PACKET_MR_ALLMULTI = 2

    def __init__(self, interface_name: str, vif_index:int):
        # RECEIVE SOCKET
        rcv_s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(InterfaceIGMP.ETH_P_IP))

        # receive only IGMP packets by setting a BPF filter
        filters = b''.join(InterfaceIGMP.FILTER_IGMP)
        b = create_string_buffer(filters)
        mem_addr_of_filters = addressof(b)
        fprog = struct.pack('HL', len(InterfaceIGMP.FILTER_IGMP), mem_addr_of_filters)
        rcv_s.setsockopt(socket.SOL_SOCKET, InterfaceIGMP.SO_ATTACH_FILTER, fprog)

        # bind to interface
        rcv_s.bind((interface_name, 0x0800))

        self.recv_socket = rcv_s

        # SEND SOCKET
        snd_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP)

        # bind to interface
        snd_s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface_name + "\0").encode('utf-8'))

        self.send_socket = snd_s

        self.interface_enabled = True
        self.interface_name = interface_name
        from igmp.RouterState import RouterState
        self.interface_state = RouterState(self)

        # virtual interface index for the multicast routing table
        self.vif_index = vif_index

        # run receive method in background
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

    def get_ip(self):
        return netifaces.ifaddresses(self.interface_name)[netifaces.AF_INET][0]['addr']

    @property
    def ip_interface(self):
        return self.get_ip()


    def send(self, data: bytes, address: str="224.0.0.1"):
        if self.interface_enabled:
            self.send_socket.sendto(data, (address, 0))

    def receive(self):
        while self.interface_enabled:
            try:
                (raw_packet, _) = self.recv_socket.recvfrom(256 * 1024)
                if raw_packet:
                    raw_packet = raw_packet[14:]
                    packet = ReceivedPacket(raw_packet, self)
                    Main.igmp.receive_handle(packet)
            except Exception:
                traceback.print_exc()
                continue

    def remove(self):
        self.interface_enabled = False
        self.recv_socket.close()
        self.send_socket.close()
