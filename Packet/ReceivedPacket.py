import struct
from Packet.Packet import Packet
from Packet.PacketIpHeader import PacketIpHeader
from Packet.PacketPimHeader import PacketPimHeader
from Packet.PacketPimOption import PacketPimOption
from utils import checksum


class ReceivedPacket(Packet):
    def __init__(self, raw_packet, interface):
        self.interface = interface
        #Parse ao packet e preencher objeto Packet

        x = ReceivedPacket.parseIpHdr(raw_packet[:PacketIpHeader.IP_HDR_LEN])
        print(x["HLEN"])
        msg_without_ip_hdr = raw_packet[x["HLEN"]:]
        self.ip_header = PacketIpHeader(x["SRC"])
        # print(msg_without_ip_hdr)

        pim_hdr = ReceivedPacket.parsePimHdr(msg_without_ip_hdr[0:PacketPimHeader.PIM_HDR_LEN])
        msg_to_checksum = msg_without_ip_hdr[0:2] + b'\x00\x00' + msg_without_ip_hdr[4:]
        print("checksum calculated: " + str(checksum(msg_to_checksum)))
        if checksum(msg_to_checksum) != pim_hdr["CHECKSUM"]:
            print("wrong checksum")
            return  # TODO: maybe excepcao
        print(pim_hdr)
        self.pim_header = PacketPimHeader(pim_hdr["TYPE"])
        if pim_hdr["TYPE"] == 0:  # hello
            pim_options = ReceivedPacket.parsePimHdrOpts(msg_without_ip_hdr[PacketPimHeader.PIM_HDR_LEN:])
            print(pim_options)
            for option in pim_options:
                self.pim_header.add_option(PacketPimOption(option["OPTION TYPE"], option["OPTION VALUE"]))
        print(self.bytes())

    def parseIpHdr(msg):
        (verhlen, tos, iplen, ipid, frag, ttl, proto, cksum, src, dst) = \
            struct.unpack(PacketIpHeader.IP_HDR, msg)

        ver = (verhlen & 0xf0) >> 4
        hlen = (verhlen & 0x0f) * 4

        return {"VER": ver,
                "HLEN": hlen,
                "TOS": tos,
                "IPLEN": iplen,
                "IPID": ipid,
                "FRAG": frag,
                "TTL": ttl,
                "PROTO": proto,
                "CKSUM": cksum,
                "SRC": src,
                "DST": dst
                }

    def parsePimHdr(msg):
        #print("parsePimHdr: ", msg.encode("hex"))
        print("parsePimHdr: ", msg)
        (pim_ver_type, reserved, checksum) = struct.unpack(PacketPimHeader.PIM_HDR, msg)

        print(pim_ver_type, reserved, checksum)
        return {"PIM VERSION": (pim_ver_type & 0xF0) >> 4,
                "TYPE": pim_ver_type & 0x0F,
                "RESERVED": reserved,
                "CHECKSUM": checksum
                }

    def parsePimHdrOpts(msg):
        options_list = []
        # print(msg)
        while msg != b'':
            (option_type, option_length) = struct.unpack(PacketPimOption.PIM_HDR_OPTS, msg[:PacketPimOption.PIM_HDR_OPTS_LEN])
            print(option_type, option_length)
            msg = msg[PacketPimOption.PIM_HDR_OPTS_LEN:]
            print(msg)
            (option_value,) = struct.unpack("! " + str(option_length) + "s", msg[:option_length])
            option_value_number = int.from_bytes(option_value, byteorder='big')
            print("option value: ", option_value_number)
            options_list.append({"OPTION TYPE": option_type,
                                 "OPTION LENGTH": option_length,
                                 "OPTION VALUE": option_value_number
                                 })
            msg = msg[option_length:]
        return options_list
