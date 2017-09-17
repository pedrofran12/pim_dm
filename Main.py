import netifaces
import time
from prettytable import PrettyTable

from Interface import Interface
from InterfaceIGMP import InterfaceIGMP
from Kernel import Kernel
from Neighbor import Neighbor
from threading import Lock

interfaces = {}  # interfaces with multicast routing enabled
igmp_interfaces = {}  # igmp interfaces
neighbors = {}  # multicast router neighbors
neighbors_lock = Lock()
protocols = {}
kernel = None
igmp = None

def add_interface(interface_name, pim=False, igmp=False):
    global interfaces
    if pim is True and interface_name not in interfaces:
        interface = Interface(interface_name)
        interfaces[interface_name] = interface
        protocols[0].force_send(interface)
    if igmp is True and interface_name not in igmp_interfaces:
        interface = InterfaceIGMP(interface_name)
        igmp_interfaces[interface_name] = interface

def remove_interface(interface_name, pim=False, igmp=False):
    global interfaces
    global neighbors
    if pim is True and ((interface_name in interfaces) or interface_name == "*"):
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

    if igmp is True and ((interface_name in igmp_interfaces) or interface_name == "*"):
        if interface_name == "*":
            interface_name = list(igmp_interfaces.keys())
        else:
            interface_name = [interface_name]
        for if_name in interface_name:
            igmp_interfaces[if_name].remove()
            del igmp_interfaces[if_name]
        print("removido interface")



def add_neighbor(contact_interface, ip, random_number, hello_hold_time):
    global neighbors
    with neighbors_lock:
        if ip not in neighbors:
            print("ADD NEIGHBOR")
            n = Neighbor(contact_interface, ip, random_number, hello_hold_time)
            neighbors[ip] = n
            protocols[0].force_send(contact_interface)
            # todo check neighbor in interface
            contact_interface.neighbors[ip] = n


def get_neighbor(ip) -> Neighbor:
    global neighbors
    with neighbors_lock:
        if ip not in neighbors:
            return None
        return neighbors[ip]

def remove_neighbor(ip):
    global neighbors
    with neighbors_lock:
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
        pckt = Packet(payload=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())

        ph = PacketPimJoinPrune("ff08::1", 210)
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("2001:1:a:b:c::1", ["1.1.1.1", "2001:1:a:b:c::2"], []))
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.123", ["1.1.1.1"], ["2001:1:a:b:c::3"]))
        pckt = Packet(payload=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())

        from Packet.PacketPimAssert import PacketPimAssert
        ph = PacketPimAssert("224.12.12.12", "10.0.0.2", 210, 2)
        pckt = Packet(payload=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())


        from Packet.PacketPimGraft import PacketPimGraft
        ph = PacketPimGraft("10.0.0.13", 210)
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.124", ["1.1.1.2", "10.1.1.2"], []))
        pckt = Packet(payload=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())



    t = PrettyTable(['Interface', 'IP', 'PIM/IMGP Enabled', 'IGMP State'])
    for interface in netifaces.interfaces():
        try:
            # TODO: fix same interface with multiple ips
            ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
            pim_enabled = interface in interfaces
            igmp_enabled = interface in igmp_interfaces
            enabled = str(pim_enabled) + "/" + str(igmp_enabled)
            if igmp_enabled:
                state = igmp_interfaces[interface].interface_state.print_state()
            else:
                state = "-"
            t.add_row([interface, ip, enabled, state])
        except Exception:
            continue
    print(t)
    return str(t)


def list_igmp_state():
    t = PrettyTable(['Interface', 'RouterState', 'Group Adress', 'GroupState'])
    for (interface_name, interface_obj) in list(igmp_interfaces.items()):
        interface_state = interface_obj.interface_state
        state_txt = interface_state.print_state()
        print(interface_state.group_state.items())

        for (group_addr, group_state) in list(interface_state.group_state.items()):
            print(group_addr)
            group_state_txt = group_state.print_state()
            t.add_row([interface_name, state_txt, group_addr, group_state_txt])
    return str(t)


def main(interfaces_to_add=[]):
    from Hello import Hello
    from IGMP import IGMP
    from Assert import Assert
    from JoinPrune import JoinPrune

    Hello()
    Assert()
    JoinPrune()
    global kernel
    kernel = Kernel()

    global igmp
    igmp = IGMP()
    for interface in interfaces_to_add:
        add_interface(interface)
