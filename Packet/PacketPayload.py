import abc


class PacketPayload(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def bytes(self) -> bytes:
        """Get packet payload in bytes format"""

    @abc.abstractmethod
    def __len__(self):
        """Get packet payload length"""

    @staticmethod
    @abc.abstractmethod
    def parse_bytes(data: bytes):
        """From bytes create a object payload"""
