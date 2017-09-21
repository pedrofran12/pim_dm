import socket
import struct
import threading
import netifaces
from Packet.ReceivedPacket import ReceivedPacket
import Main
import traceback
if not hasattr(socket, 'SO_BINDTODEVICE'):
    socket.SO_BINDTODEVICE = 25


class InterfaceIGMP(object):
    ETH_P_IP = 0x0800		# Internet Protocol packet

    PACKET_MR_ALLMULTI = 2

    def __init__(self, interface_name: str):
        # RECEIVE SOCKET
        rcv_s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(InterfaceIGMP.ETH_P_IP))

        # allow all multicast packets
        rcv_s.setsockopt(socket.SOL_SOCKET, InterfaceIGMP.PACKET_MR_ALLMULTI, struct.pack("i HH BBBBBBBB", 0, InterfaceIGMP.PACKET_MR_ALLMULTI, 0,    0,0,0,0,0,0,0,0))

        # bind to interface
        rcv_s.bind((interface_name, 0))

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

        # run receive method in background
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

    def get_ip(self):
        return netifaces.ifaddresses(self.interface_name)[netifaces.AF_INET][0]['addr']

    def send(self, data: bytes, address: str="224.0.0.1"):
        if self.interface_enabled:
            self.send_socket.sendto(data, (address, 0))

    def receive(self):
        while self.interface_enabled:
            try:
                (raw_packet, x) = self.recv_socket.recvfrom(256 * 1024)
                if raw_packet:
                    raw_packet = raw_packet[14:]
                    from Packet.PacketIpHeader import PacketIpHeader
                    (verhlen, tos, iplen, ipid, frag, ttl, proto, cksum, src, dst) = \
                        struct.unpack(PacketIpHeader.IP_HDR, raw_packet[:PacketIpHeader.IP_HDR_LEN])
                    #print(proto)

                    if proto != socket.IPPROTO_IGMP:
                        continue
                    #print((raw_packet, x))
                    packet = ReceivedPacket(raw_packet, self)
                    Main.igmp.receive_handle(packet)
            except Exception:
                traceback.print_exc()
                continue

    def remove(self):
        self.interface_enabled = False
        self.recv_socket.close()
        self.send_socket.close()
