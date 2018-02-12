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


def add_pim_interface(interface_name, state_refresh_capable:bool=False):
    kernel.create_pim_interface(interface_name=interface_name, state_refresh_capable=state_refresh_capable)


def add_igmp_interface(interface_name):
    kernel.create_igmp_interface(interface_name=interface_name)

'''
def add_interface(interface_name, pim=False, igmp=False):
    #if pim is True and interface_name not in interfaces:
    #    interface = InterfacePim(interface_name)
    #    interfaces[interface_name] = interface
    #    interface.create_virtual_interface()
    #if igmp is True and interface_name not in igmp_interfaces:
    #    interface = InterfaceIGMP(interface_name)
    #    igmp_interfaces[interface_name] = interface
    kernel.create_interface(interface_name=interface_name, pim=pim, igmp=igmp)
    #if pim:
    #    interfaces[interface_name] = kernel.pim_interface[interface_name]
    #if igmp:
    #    igmp_interfaces[interface_name] = kernel.igmp_interface[interface_name]
'''

def remove_interface(interface_name, pim=False, igmp=False):
    #if pim is True and ((interface_name in interfaces) or interface_name == "*"):
    #    if interface_name == "*":
    #        interface_name_list = list(interfaces.keys())
    #    else:
    #        interface_name_list = [interface_name]
    #    for if_name in interface_name_list:
    #        interface_obj = interfaces.pop(if_name)
    #        interface_obj.remove()
    #        #interfaces[if_name].remove()
    #        #del interfaces[if_name]
    #    print("removido interface")
    #    print(interfaces)

    #if igmp is True and ((interface_name in igmp_interfaces) or interface_name == "*"):
    #    if interface_name == "*":
    #        interface_name_list = list(igmp_interfaces.keys())
    #    else:
    #        interface_name_list = [interface_name]
    #    for if_name in interface_name_list:
    #        igmp_interfaces[if_name].remove()
    #        del igmp_interfaces[if_name]
    #    print("removido interface")
    #    print(igmp_interfaces)
    kernel.remove_interface(interface_name, pim=pim, igmp=igmp)

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

    t = PrettyTable(['SourceIP', 'GroupIP', 'Interface', 'PruneState', 'AssertState', 'LocalMembership', "Is Forwarding?"])
    for entry in routing_entries:
        ip = entry.source_ip
        group = entry.group_ip
        upstream_if_index = entry.inbound_interface_index

        for index in vif_indexes:
            interface_state = entry.interface_state[index]
            interface_name = kernel.vif_index_to_name_dic[index]
            local_membership = type(interface_state._local_membership_state).__name__
            try:
                if index != upstream_if_index:
                    prune_state = type(interface_state._prune_state).__name__
                    assert_state = type(interface_state._assert_state).__name__
                    is_forwarding = interface_state.is_forwarding()
                else:
                    prune_state = type(interface_state._graft_prune_state).__name__
                    assert_state = "-"
                    is_forwarding = "upstream"
            except:
                prune_state = "-"
                assert_state = "-"

            t.add_row([ip, group, interface_name, prune_state, assert_state, local_membership, is_forwarding])
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
    from GraftAck import GraftAck
    from Graft import Graft
    from StateRefresh import StateRefresh

    Hello()
    Assert()
    JoinPrune()
    Graft()
    GraftAck()
    StateRefresh()
    global kernel
    kernel = Kernel()

    global igmp
    igmp = IGMP()

    global u
    u = UnicastRouting.UnicastRouting()

    global interfaces
    global igmp_interfaces
    interfaces = kernel.pim_interface
    igmp_interfaces = kernel.igmp_interface
