import netifaces
import time
from prettytable import PrettyTable

from Interface import Interface
from Neighbor import Neighbor

interfaces = {}  # interfaces with multicast routing enabled
neighbors = {}  # multicast router neighbors
protocols = {}


def add_interface(ip):
    global interfaces
    if ip not in interfaces:
        interface = Interface(ip)
        interfaces[ip] = interface
        protocols[0].force_send(interface)

# TODO: verificar melhor este metodo:
def remove_interface(ip):
    # TODO remover neighbors desta interface
    global interfaces
    global neighbors
    if ip in interfaces:
        for (ip_neighbor, neighbor) in list(neighbors.items()):
            # TODO ver melhor este algoritmo
            if neighbor.contact_interface == interfaces[ip]:
                neighbor.remove()
        protocols[0].force_send_remove(interfaces[ip])
        interfaces[ip].remove()
        del interfaces[ip]
        print("removido interface")

def add_neighbor(contact_interface, ip, random_number, keep_alive_period):
    global neighbors
    if ip not in neighbors:
        print("ADD NEIGHBOR")
        neighbors[ip] = Neighbor(contact_interface, ip, random_number, keep_alive_period)
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
    t = PrettyTable(['Neighbor IP', 'KeepAlive', "Generation ID", "Uptime"])
    for ip, neighbor in list(neighbors.items()):
        uptime = check_time - neighbor.time_of_last_update
        uptime = 0 if (uptime < 0) else uptime

        t.add_row([ip, neighbor.keep_alive_period, neighbor.generation_id, time.strftime("%H:%M:%S", time.gmtime(uptime))])
    print(t)
    return str(t)

def list_enabled_interfaces():
    global interfaces

    for interface in interfaces:
        from Packet.Packet import Packet
        from Packet.PacketPimHeader import PacketPimHeader
        from Packet.PacketPimJoinPrune import PacketPimJoinPrune
        from Packet.PacketPimJoinPruneMulticastGroup import PacketPimJoinPruneMulticastGroup

        ph = PacketPimJoinPrune("10.0.0.13", 210)
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.123", ["1.1.1.1"], []))
        pckt = Packet(pim_header=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())



    t = PrettyTable(['Interface', 'IP', 'Enabled'])
    for interface in netifaces.interfaces():
        # TODO: fix same interface with multiple ips
        ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        status = ip in interfaces
        t.add_row([interface, ip, status])
    print(t)
    return str(t)

def main(ip_interfaces_to_add=[]):
    from Hello import Hello
    Hello()

    for ip in ip_interfaces_to_add:
        add_interface(ip)
