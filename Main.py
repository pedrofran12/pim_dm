import netifaces
import time
from prettytable import PrettyTable

from Interface import Interface
from Neighbor import Neighbor

interfaces = {}  # interfaces with multicast routing enabled
neighbors = {}  # multicast router neighbors
protocols = {}


def add_interface(interface_name):
    global interfaces
    if interface_name not in interfaces:
        interface = Interface(interface_name)
        interfaces[interface_name] = interface
        protocols[0].force_send(interface)


def remove_interface(interface_name):
    global interfaces
    global neighbors
    if (interface_name in interfaces) or interface_name == "*":
        if interface_name == "*":
            interface_name = list(interfaces.keys())
        else:
            interface_name = [interface_name]
        for if_name in interface_name:
            protocols[0].force_send_remove(interfaces[if_name])
            interfaces[if_name].remove()
            del interfaces[if_name]
        print("removido interface")

        for (ip_neighbor, neighbor) in list(neighbors.items()):
            if neighbor.contact_interface not in interfaces:
                neighbor.remove()


def add_neighbor(contact_interface, ip, random_number, hello_hold_time):
    global neighbors
    if ip not in neighbors:
        print("ADD NEIGHBOR")
        neighbors[ip] = Neighbor(contact_interface, ip, random_number, hello_hold_time)
        protocols[0].force_send(contact_interface)

def get_neighbor(ip) -> Neighbor:
    global neighbors
    if ip not in neighbors:
        return None
    return neighbors[ip]

def remove_neighbor(ip):
    global neighbors
    if ip in neighbors:
        del neighbors[ip]
        print("removido neighbor")

def add_protocol(protocol_number, protocol_obj):
    global protocols
    protocols[protocol_number] = protocol_obj

def list_neighbors():
    global neighbors
    check_time = time.time()
    t = PrettyTable(['Neighbor IP', 'Hello Hold Time', "Generation ID", "Uptime"])
    for ip, neighbor in list(neighbors.items()):
        uptime = check_time - neighbor.time_of_last_update
        uptime = 0 if (uptime < 0) else uptime

        t.add_row([ip, neighbor.hello_hold_time, neighbor.generation_id, time.strftime("%H:%M:%S", time.gmtime(uptime))])
    print(t)
    return str(t)

def list_enabled_interfaces():
    global interfaces
    # TESTE DE PIM JOIN/PRUNE
    for interface in interfaces:
        from Packet.Packet import Packet
        from Packet.PacketPimHeader import PacketPimHeader
        from Packet.PacketPimJoinPrune import PacketPimJoinPrune
        from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup

        ph = PacketPimJoinPrune("10.0.0.13", 210)
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.123", ["1.1.1.1", "10.1.1.1"], []))
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.124", ["1.1.1.2", "10.1.1.2"], []))
        pckt = Packet(pim_header=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())

        ph = PacketPimJoinPrune("ff08::1", 210)
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("2001:1:a:b:c::1", ["1.1.1.1", "2001:1:a:b:c::2"], []))
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.123", ["1.1.1.1"], ["2001:1:a:b:c::3"]))
        pckt = Packet(pim_header=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())



    t = PrettyTable(['Interface', 'IP', 'Enabled'])
    for interface in netifaces.interfaces():
        # TODO: fix same interface with multiple ips
        ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        status = interface in interfaces
        t.add_row([interface, ip, status])
    print(t)
    return str(t)

def main(interfaces_to_add=[]):
    from Hello import Hello
    Hello()

    for interface in interfaces_to_add:
        add_interface(interface)
