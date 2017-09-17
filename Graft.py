import random
from threading import Timer
from Packet.Packet import Packet
from Packet.ReceivedPacket import ReceivedPacket
from Packet.PacketPimHello import PacketPimHello
from Packet.PacketPimHeader import PacketPimHeader
from Interface import Interface
import Main
from utils import HELLO_HOLD_TIME_TIMEOUT


class Graft:
    TYPE = 6

    def __init__(self):
        Main.add_protocol(Graft.TYPE, self)

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        ip = packet.ip_header.ip_src
        print("ip = ", ip)
        pkt_join_prune = packet.payload.payload
        # TODO
        raise Exception