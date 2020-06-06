from .PacketIpHeader import PacketIpHeader
from .PacketPayload import PacketPayload


class Packet(object):
    def __init__(self, ip_header: PacketIpHeader = None, payload: PacketPayload = None):
        self.ip_header = ip_header
        self.payload = payload

    def bytes(self) -> bytes:
        return self.payload.bytes()
