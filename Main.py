import netifaces
import time
from prettytable import PrettyTable

from InterfacePIM import InterfacePim
from InterfaceIGMP import InterfaceIGMP
from Kernel import Kernel
from threading import Lock
import UnicastRouting

interfaces = {}  # interfaces with multicast routing enabled
igmp_interfaces = {}  # igmp interfaces
protocols = {}
kernel = None
igmp = None


def add_interface(interface_name, pim=False, igmp=False):
    if pim is True and interface_name not in interfaces:
        interface = InterfacePim(interface_name)
        interfaces[interface_name] = interface
    if igmp is True and interface_name not in igmp_interfaces:
        interface = InterfaceIGMP(interface_name)
        igmp_interfaces[interface_name] = interface


def remove_interface(interface_name, pim=False, igmp=False):
    if pim is True and ((interface_name in interfaces) or interface_name == "*"):
        if interface_name == "*":
            interface_name_list = list(interfaces.keys())
        else:
            interface_name_list = [interface_name]
        for if_name in interface_name_list:
            interface_obj = interfaces.pop(if_name)
            interface_obj.remove()
            #interfaces[if_name].remove()
            #del interfaces[if_name]
        print("removido interface")
        print(interfaces)

    if igmp is True and ((interface_name in igmp_interfaces) or interface_name == "*"):
        if interface_name == "*":
            interface_name_list = list(igmp_interfaces.keys())
        else:
            interface_name_list = [interface_name]
        for if_name in interface_name_list:
            igmp_interfaces[if_name].remove()
            del igmp_interfaces[if_name]
        print("removido interface")
        print(igmp_interfaces)


"""
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
"""

def add_protocol(protocol_number, protocol_obj):
    global protocols
    protocols[protocol_number] = protocol_obj

def list_neighbors():
    interfaces_list = interfaces.values()
    t = PrettyTable(['Interface', 'Neighbor IP', 'Hello Hold Time', "Generation ID", "Uptime"])
    check_time = time.time()
    for interface in interfaces_list:
        for neighbor in interface.get_neighbors():
            uptime = check_time - neighbor.time_of_last_update
            uptime = 0 if (uptime < 0) else uptime

            t.add_row(
                [interface.interface_name, neighbor.ip, neighbor.hello_hold_time, neighbor.generation_id, time.strftime("%H:%M:%S", time.gmtime(uptime))])
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
        ph = PacketPimGraft("10.0.0.13")
        ph.add_multicast_group(PacketPimJoinPruneMulticastGroup("239.123.123.124", ["1.1.1.2", "10.1.1.2"], []))
        pckt = Packet(payload=PacketPimHeader(ph))
        interfaces[interface].send(pckt.bytes())



    t = PrettyTable(['Interface', 'IP', 'PIM/IGMP Enabled', 'IGMP State'])
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


def list_state():
    state_text = "IGMP State:\n" + list_igmp_state() + "\n\n\n\n" + "Multicast Routing State:\n" + list_routing_state()
    return state_text


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


def list_routing_state():
    routing_entries = kernel.routing.values()
    vif_indexes = kernel.vif_index_to_name_dic.keys()

    t = PrettyTable(['SourceIP', 'GroupIP', 'Interface', 'PruneState', 'AssertState', "Is Forwarding?"])
    for entry in routing_entries:
        ip = entry.source_ip
        group = entry.group_ip

        for index in vif_indexes:
            interface_state = entry.interface_state[index]
            interface_name = kernel.vif_index_to_name_dic[index]
            is_forwarding = interface_state.is_forwarding()
            try:
                prune_state = type(interface_state._prune_state).__name__
                assert_state = type(interface_state._assert_state).__name__
            except:
                prune_state = "-"
                assert_state = "-"

            t.add_row([ip, group, interface_name, prune_state, assert_state, is_forwarding])
    return str(t)


def stop():
    remove_interface("*", pim=True, igmp=True)
    kernel.exit()
    UnicastRouting.stop()


def main():
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