import struct
from abc import ABCMeta
import math

class PacketPimHelloOptions(metaclass=ABCMeta):
    PIM_HDR_OPTS = "! HH"
    PIM_HDR_OPTS_LEN = struct.calcsize(PIM_HDR_OPTS)
    '''
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |              Type             |             Length            |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    '''
    def __init__(self, type: int, length: int):
        self.type = type
        self.length = length

    def bytes(self) -> bytes:
        return struct.pack(PacketPimHelloOptions.PIM_HDR_OPTS, self.type, self.length)

    def __len__(self):
        return self.PIM_HDR_OPTS_LEN + self.length

    @staticmethod
    def parse_bytes(data: bytes, type:int = None, length:int = None):
        (type, length) = struct.unpack(PacketPimHelloOptions.PIM_HDR_OPTS,
                                        data[:PacketPimHelloOptions.PIM_HDR_OPTS_LEN])
        #print("TYPE:", type)
        #print("LENGTH:", length)
        data = data[PacketPimHelloOptions.PIM_HDR_OPTS_LEN:]
        #return PIM_MSG_TYPES[type](data)
        return PIM_MSG_TYPES.get(type, PacketPimHelloUnknown).parse_bytes(data, type, length)


class PacketPimHelloStateRefreshCapable(PacketPimHelloOptions):
    PIM_HDR_OPT = "! BBH"
    PIM_HDR_OPT_LEN = struct.calcsize(PIM_HDR_OPT)
    '''
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |  Version = 1  |   Interval    |            Reserved           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    '''
    VERSION = 1

    def __init__(self, interval: int):
        super().__init__(type=21, length=4)
        self.interval = interval

    def bytes(self) -> bytes:
        return super().bytes() + struct.pack(self.PIM_HDR_OPT, self.VERSION, self.interval, 0)

    @staticmethod
    def parse_bytes(data: bytes, type:int = None, length:int = None):
        if type is None or length is None:
            raise Exception
        (version, interval, _) = struct.unpack(PacketPimHelloStateRefreshCapable.PIM_HDR_OPT,
                                                     data[:PacketPimHelloStateRefreshCapable.PIM_HDR_OPT_LEN])
        return PacketPimHelloStateRefreshCapable(interval)



class PacketPimHelloLANPruneDelay(PacketPimHelloOptions):
    PIM_HDR_OPT = "! HH"
    PIM_HDR_OPT_LEN = struct.calcsize(PIM_HDR_OPT)
    '''
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |T|       LAN Prune Delay       |       Override Interval       |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    '''
    def __init__(self, lan_prune_delay: float, override_interval: float):
        super().__init__(type=2, length=4)
        self.lan_prune_delay = 0x7FFF & math.ceil(lan_prune_delay)
        self.override_interval = math.ceil(override_interval)

    def bytes(self) -> bytes:
        return super().bytes() + struct.pack(self.PIM_HDR_OPT, self.lan_prune_delay, self.override_interval)

    @staticmethod
    def parse_bytes(data: bytes, type:int = None, length:int = None):
        if type is None or length is None:
            raise Exception
        (lan_prune_delay, override_interval) = struct.unpack(PacketPimHelloLANPruneDelay.PIM_HDR_OPT,
                                                     data[:PacketPimHelloLANPruneDelay.PIM_HDR_OPT_LEN])
        lan_prune_delay = lan_prune_delay & 0x7FFF
        return PacketPimHelloLANPruneDelay(lan_prune_delay=lan_prune_delay, override_interval=override_interval)



class PacketPimHelloHoldtime(PacketPimHelloOptions):
    PIM_HDR_OPT = "! H"
    PIM_HDR_OPT_LEN = struct.calcsize(PIM_HDR_OPT)
    '''
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |            Hold Time          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    '''
    def __init__(self, holdtime: int or float):
        super().__init__(type=1, length=2)
        self.holdtime = int(holdtime)

    def bytes(self) -> bytes:
        return super().bytes() + struct.pack(self.PIM_HDR_OPT, self.holdtime)

    @staticmethod
    def parse_bytes(data: bytes, type:int = None, length:int = None):
        if type is None or length is None:
            raise Exception
        (holdtime, ) = struct.unpack(PacketPimHelloHoldtime.PIM_HDR_OPT,
                                     data[:PacketPimHelloHoldtime.PIM_HDR_OPT_LEN])
        #print("HOLDTIME:", holdtime)
        return PacketPimHelloHoldtime(holdtime=holdtime)



class PacketPimHelloGenerationID(PacketPimHelloOptions):
    PIM_HDR_OPT = "! L"
    PIM_HDR_OPT_LEN = struct.calcsize(PIM_HDR_OPT)
    '''
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Generation ID                         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    '''
    def __init__(self, generation_id: int):
        super().__init__(type=20, length=4)
        self.generation_id = generation_id

    def bytes(self) -> bytes:
        return super().bytes() + struct.pack(self.PIM_HDR_OPT, self.generation_id)

    @staticmethod
    def parse_bytes(data: bytes, type:int = None, length:int = None):
        if type is None or length is None:
            raise Exception
        (generation_id, ) = struct.unpack(PacketPimHelloGenerationID.PIM_HDR_OPT,
                                     data[:PacketPimHelloGenerationID.PIM_HDR_OPT_LEN])
        #print("GenerationID:", generation_id)
        return PacketPimHelloGenerationID(generation_id=generation_id)


class PacketPimHelloUnknown(PacketPimHelloOptions):
    PIM_HDR_OPT = "! L"
    PIM_HDR_OPT_LEN = struct.calcsize(PIM_HDR_OPT)
    '''
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                            Unknown                            |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    '''
    def __init__(self, type, length):
        super().__init__(type=type, length=length)
        #print("PIM Hello Option Unknown... TYPE=", type, "LENGTH=", length)

    def bytes(self) -> bytes:
        raise Exception

    @staticmethod
    def parse_bytes(data: bytes, type:int = None, length:int = None):
        if type is None or length is None:
            raise Exception
        return PacketPimHelloUnknown(type, length)





PIM_MSG_TYPES = {1: PacketPimHelloHoldtime,
                 2: PacketPimHelloLANPruneDelay,
                 20: PacketPimHelloGenerationID,
                 21: PacketPimHelloStateRefreshCapable,
                 }
