import time
from Main import Main

#indicar ips das interfaces pim
m = Main()
m.main(["10.0.0.1"])
'''
from Packet.PacketPimHeader import *
ph = PacketPimHeader(0)
po = PacketPimOption(1, 12408)
ph.add_option(po)
ph.add_option(PacketPimOption(20, 813183289))
packet = Packet(pim_header=ph)
m.interfaces["10.0.0.1"].send(packet.bytes())'''
time.sleep(100)
