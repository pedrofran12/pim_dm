import os
import sys
import time
import netifaces
import logging
import logging.handlers
from prettytable import PrettyTable
from pimdm.tree import pim_globals

from pimdm import UnicastRouting
from pimdm.TestLogger import RootFilter

interfaces = {}  # interfaces with multicast routing enabled
igmp_interfaces = {}  # igmp interfaces
interfaces_v6 = {}  # pim v6 interfaces
mld_interfaces = {}  # mld interfaces
kernel = None
kernel_v6 = None
unicast_routing = None
logger = None


def add_pim_interface(interface_name, state_refresh_capable: bool = False, ipv4=True, ipv6=False):
    if interface_name == "*":
        for interface_name in netifaces.interfaces():
            add_pim_interface(interface_name, ipv4, ipv6)
        return

    if ipv4 and kernel is not None:
        kernel.create_pim_interface(interface_name=interface_name, state_refresh_capable=state_refresh_capable)
    if ipv6 and kernel_v6 is not None:
        kernel_v6.create_pim_interface(interface_name=interface_name, state_refresh_capable=state_refresh_capable)


def add_membership_interface(interface_name, ipv4=True, ipv6=False):
    if interface_name == "*":
        for interface_name in netifaces.interfaces():
            add_membership_interface(interface_name, ipv4, ipv6)
        return

    if ipv4 and kernel is not None:
        kernel.create_membership_interface(interface_name=interface_name)
    if ipv6 and kernel_v6 is not None:
        kernel_v6.create_membership_interface(interface_name=interface_name)


def remove_interface(interface_name, pim=False, membership=False, ipv4=True, ipv6=False):
    if interface_name == "*":
        for interface_name in netifaces.interfaces():
            remove_interface(interface_name, pim, membership, ipv4, ipv6)
        return

    if ipv4 and kernel is not None:
        kernel.remove_interface(interface_name, pim=pim, membership=membership)
    if ipv6 and kernel_v6 is not None:
        kernel_v6.remove_interface(interface_name, pim=pim, membership=membership)


def list_neighbors(ipv4=False, ipv6=False):
    if ipv4:
        interfaces_list = interfaces.values()
    elif ipv6:
        interfaces_list = interfaces_v6.values()
    else:
        return "Unknown IP family"

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


def list_enabled_interfaces(ipv4=False, ipv6=False):
    if ipv4:
        t = PrettyTable(['Interface', 'IP', 'PIM/IGMP Enabled', 'State Refresh Enabled', 'IGMP State'])
        family = netifaces.AF_INET
        pim_interfaces = interfaces
        membership_interfaces = igmp_interfaces
    elif ipv6:
        t = PrettyTable(['Interface', 'IP', 'PIM/MLD Enabled', 'State Refresh Enabled', 'MLD State'])
        family = netifaces.AF_INET6
        pim_interfaces = interfaces_v6
        membership_interfaces = mld_interfaces
    else:
        return "Unknown IP family"

    for interface in netifaces.interfaces():
        try:
            # TODO: fix same interface with multiple ips
            ip = netifaces.ifaddresses(interface)[family][0]['addr']
            pim_enabled = interface in pim_interfaces
            membership_enabled = interface in membership_interfaces
            enabled = str(pim_enabled) + "/" + str(membership_enabled)
            state_refresh_enabled = "-"
            if pim_enabled:
                state_refresh_enabled = pim_interfaces[interface].is_state_refresh_enabled()
            membership_state = "-"
            if membership_enabled:
                membership_state = membership_interfaces[interface].interface_state.print_state()
            t.add_row([interface, ip, enabled, state_refresh_enabled, membership_state])
        except Exception:
            continue
    print(t)
    return str(t)


def list_state(ipv4=True, ipv6=False):
    state_text = ""
    if ipv4:
        state_text = "IGMP State:\n{}\n\n\n\nMulticast Routing State:\n{}"
    elif ipv6:
        state_text = "MLD State:\n{}\n\n\n\nMulticast Routing State:\n{}"
    else:
        return state_text
    return state_text.format(list_membership_state(ipv4, ipv6), list_routing_state(ipv4, ipv6))


def list_membership_state(ipv4=True, ipv6=False):
    t = PrettyTable(['Interface', 'RouterState', 'Group Adress', 'GroupState'])
    if ipv4:
        membership_interfaces = igmp_interfaces
    elif ipv6:
        membership_interfaces = mld_interfaces
    else:
        membership_interfaces = {}

    for (interface_name, interface_obj) in list(membership_interfaces.items()):
        interface_state = interface_obj.interface_state
        state_txt = interface_state.print_state()
        print(interface_state.group_state.items())

        for (group_addr, group_state) in list(interface_state.group_state.items()):
            print(group_addr)
            group_state_txt = group_state.print_state()
            t.add_row([interface_name, state_txt, group_addr, group_state_txt])
    return str(t)


def list_routing_state(ipv4=False, ipv6=False):
    if ipv4:
        routes = kernel.routing.values()
        vif_indexes = kernel.vif_index_to_name_dic.keys()
        dict_index_to_name = kernel.vif_index_to_name_dic
    elif ipv6:
        routes = kernel_v6.routing.values()
        vif_indexes = kernel_v6.vif_index_to_name_dic.keys()
        dict_index_to_name = kernel_v6.vif_index_to_name_dic
    else:
        raise Exception("Unknown IP family")

    routing_entries = []
    for a in list(routes):
        for b in list(a.values()):
            routing_entries.append(b)

    t = PrettyTable(['SourceIP', 'GroupIP', 'Interface', 'OriginatorState', 'PruneState', 'AssertState', 'LocalMembership', "Is Forwarding?"])
    for entry in routing_entries:
        ip = entry.source_ip
        group = entry.group_ip
        upstream_if_index = entry.inbound_interface_index

        for index in vif_indexes:
            interface_state = entry.interface_state[index]
            interface_name = dict_index_to_name[index]
            local_membership = type(interface_state._local_membership_state).__name__
            try:
                assert_state = type(interface_state._assert_state).__name__
                if index != upstream_if_index:
                    prune_state = type(interface_state._prune_state).__name__
                    originator_state = "-"
                    is_forwarding = interface_state.is_forwarding()
                else:
                    prune_state = type(interface_state._graft_prune_state).__name__
                    is_forwarding = "upstream"
                    originator_state = type(interface_state._originator_state).__name__
            except:
                originator_state = "-"
                prune_state = "-"
                assert_state = "-"
                is_forwarding = "-"

            t.add_row([ip, group, interface_name, originator_state, prune_state, assert_state, local_membership, is_forwarding])
    return str(t)


def list_instances():
    """
    List instance information
    """
    t = "{}|{}|{}"
    return t.format(os.getpid(), pim_globals.MULTICAST_TABLE_ID, pim_globals.UNICAST_TABLE_ID)


def stop():
    remove_interface("*", pim=True, membership=True, ipv4=True, ipv6=True)
    if kernel is not None:
        kernel.exit()
    if kernel_v6 is not None:
        kernel_v6.exit()
    unicast_routing.stop()


def test(router_name, server_logger_ip):
    global logger
    socketHandler = logging.handlers.SocketHandler(server_logger_ip,
                                                   logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    # don't bother with a formatter, since a socket handler sends the event as
    # an unformatted pickle
    socketHandler.addFilter(RootFilter(router_name))
    logger.addHandler(socketHandler)


def get_config():
    """
    Get live configuration of PIM-DM process
    """
    try:
        from . import Config
        return Config.get_yaml_file()
    except ModuleNotFoundError:
        return "PYYAML needs to be installed. Execute \"pip3 install pyyaml\""
    except ImportError:
        return "PYYAML needs to be installed. Execute \"pip3 install pyyaml\""


def set_config(file_path):
    """
    Set configuration of PIM-DM process
    """
    from . import Config
    try:
        Config.parse_config_file(file_path)
    except:
        import traceback
        traceback.print_exc()


def drop(interface_name, packet_type):
    interfaces.get(interface_name).drop_packet_type = packet_type


def enable_ipv6_kernel():
    """
    Function to explicitly enable IPv6 Multicast Routing stack.
    This may not be enabled by default due to some old linux kernels that may not have IPv6 stack or do not have
    IPv6 multicast routing support
    """
    global kernel_v6
    from pimdm.Kernel import Kernel6
    kernel_v6 = Kernel6()

    global interfaces_v6
    global mld_interfaces
    interfaces_v6 = kernel_v6.pim_interface
    mld_interfaces = kernel_v6.membership_interface


def main():
    # logging
    global logger
    logger = logging.getLogger('pim')
    mld_logger = logging.getLogger('mld')
    igmp_logger = logging.getLogger('igmp')
    logger.setLevel(logging.DEBUG)
    igmp_logger.setLevel(logging.DEBUG)
    mld_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RootFilter(""))
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)-20s %(name)-50s %(tree)-35s %(vif)-2s %(interfacename)-5s '
                                           '%(routername)-2s %(message)s'))
    logger.addHandler(handler)
    igmp_logger.addHandler(handler)
    mld_logger.addHandler(handler)

    global kernel
    from pimdm.Kernel import Kernel4
    kernel = Kernel4()

    global unicast_routing
    unicast_routing = UnicastRouting.UnicastRouting()

    global interfaces
    global igmp_interfaces
    interfaces = kernel.pim_interface
    igmp_interfaces = kernel.membership_interface

    try:
        enable_ipv6_kernel()
    except:
        pass
