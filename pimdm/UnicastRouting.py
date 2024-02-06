import socket
import ipaddress
import logging
from threading import RLock
from socket import if_indextoname
from pyroute2 import IPDB
from pimdm.tree import pim_globals


def get_route(ip_dst: str):
    return UnicastRouting.get_route(ip_dst)


def get_metric(ip_dst: str):
    return UnicastRouting.get_metric(ip_dst)


def check_rpf(ip_dst):
    return UnicastRouting.check_rpf(ip_dst)


def get_unicast_info(ip_dst):
    return UnicastRouting.get_unicast_info(ip_dst)


class UnicastRouting(object):
    ipdb = None
    lock = RLock()

    def __init__(self):
        #UnicastRouting.ipr = IPRoute()
        UnicastRouting.ipdb = IPDB()
        self._ipdb = UnicastRouting.ipdb
        self._ipdb.register_callback(UnicastRouting.unicast_changes, mode="post")


    # get metrics (routing preference and cost) to IP ip_dst
    @staticmethod
    def get_metric(ip_dst: str):
        (metric_administrative_distance, metric_cost, _, _, mask) = UnicastRouting.get_unicast_info(ip_dst)
        return (metric_administrative_distance, metric_cost, mask)

    # get output interface IP, used to send data to IP ip_dst
    # (root interface IP to ip_dst)
    @staticmethod
    def check_rpf(ip_dst):
        # vif index of rpf interface
        return UnicastRouting.get_unicast_info(ip_dst)[3]

    @staticmethod
    def get_route(ip_dst: str):
        ip_version = ipaddress.ip_address(ip_dst).version
        if ip_version == 4:
            family = socket.AF_INET
            full_mask = 32
        elif ip_version == 6:
            family = socket.AF_INET6
            full_mask = 128
        else:
            raise Exception("Unknown IP version")
        info = None
        with UnicastRouting.lock:
            ipdb = UnicastRouting.ipdb  # type:IPDB

            for mask_len in range(full_mask, 0, -1):
                dst_network = str(ipaddress.ip_interface(ip_dst + "/" + str(mask_len)).network)

                logging.debug(dst_network)
                if dst_network in ipdb.routes.tables[pim_globals.UNICAST_TABLE_ID]:
                    logging.debug(info)
                    if ipdb.routes[{'dst': dst_network, 'family': family,
                                    'table': pim_globals.UNICAST_TABLE_ID}]['ipdb_scope'] != 'gc':
                        info = ipdb.routes[{'dst': dst_network, 'family': family, 'table': pim_globals.UNICAST_TABLE_ID}]
                    break
                else:
                    continue
            if not info:
                logging.debug("0.0.0.0/0 or ::/0")
                if "default" in ipdb.routes.tables[pim_globals.UNICAST_TABLE_ID]:
                    info = ipdb.routes[{'dst': 'default', 'family': family, 'table': pim_globals.UNICAST_TABLE_ID}]
            logging.debug(info)
            return info

    @staticmethod
    def get_unicast_info(ip_dst):
        metric_administrative_distance = 0xFFFFFFFF
        metric_cost = 0xFFFFFFFF
        rpf_node = ip_dst
        oif = None
        mask = 0
        with UnicastRouting.lock:
            unicast_route = UnicastRouting.get_route(ip_dst)
            if unicast_route is not None:
                oif = unicast_route.get("oif")
                next_hop = unicast_route["gateway"]
                multipaths = unicast_route["multipath"]
                #prefsrc = unicast_route.get("prefsrc")

                #rpf_node = ip_dst if (next_hop is None and prefsrc is not None) else next_hop
                rpf_node = next_hop if next_hop is not None else ip_dst
                if ipaddress.ip_address(ip_dst).version == 4:
                    highest_ip = ipaddress.ip_address("0.0.0.0")
                else:
                    highest_ip = ipaddress.ip_address("::")
                for m in multipaths:
                    if m.get("gateway", None) is None:
                        oif = m.get('oif')
                        rpf_node = ip_dst
                        break
                    elif ipaddress.ip_address(m["gateway"]) > highest_ip:
                        highest_ip = ipaddress.ip_address(m["gateway"])
                        oif = m.get('oif')
                        rpf_node = m["gateway"]

                metric_administrative_distance = unicast_route["proto"]
                metric_cost = unicast_route["priority"]
                metric_cost = metric_cost if metric_cost is not None else 0
                mask = unicast_route["dst_len"]

        interface_name = None if oif is None else if_indextoname(int(oif))
        from pimdm import Main
        if ipaddress.ip_address(ip_dst).version == 4:
            rpf_if = Main.kernel.vif_name_to_index_dic.get(interface_name)
        else:
            rpf_if = Main.kernel_v6.vif_name_to_index_dic.get(interface_name)
        return (metric_administrative_distance, metric_cost, rpf_node, rpf_if, mask)

    @staticmethod
    def unicast_changes(ipdb, msg, action):
        """
        Kernel notified about a change
        Verify the type of change and recheck all trees if necessary
        """
        logging.debug("unicast change?")
        logging.debug(action)
        UnicastRouting.lock.acquire()
        family = msg['family']
        if action == "RTM_NEWROUTE" or action == "RTM_DELROUTE":
            logging.debug(ipdb.routes)
            mask_len = msg["dst_len"]
            network_address = None
            attrs = msg["attrs"]
            logging.debug(attrs)
            for (key, value) in attrs:
                logging.debug((key, value))
                if key == "RTA_DST":
                    network_address = value
                    break
            if network_address is None and family == socket.AF_INET:
                network_address = "0.0.0.0"
            elif network_address is None and family == socket.AF_INET6:
                network_address = "::"
            logging.debug(network_address)
            logging.debug(mask_len)
            logging.debug(network_address + "/" + str(mask_len))
            subnet = ipaddress.ip_network(network_address + "/" + str(mask_len))
            logging.debug(str(subnet))
            UnicastRouting.lock.release()
            from pimdm import Main
            if family == socket.AF_INET:
                Main.kernel.notify_unicast_changes(subnet)
            elif family == socket.AF_INET6:
                Main.kernel_v6.notify_unicast_changes(subnet)
            '''
        elif action == "RTM_NEWADDR" or action == "RTM_DELADDR":
            print(action)
            print(msg)
            interface_name = None
            attrs = msg["attrs"]
            for (key, value) in attrs:
                print((key, value))
                if key == "IFA_LABEL":
                    interface_name = value
                    break
            UnicastRouting.lock.release()
            try:
                Main.kernel.notify_interface_changes(interface_name)
            except:
                import traceback
                traceback.print_exc()
                pass
            subnet = ipaddress.ip_network("0.0.0.0/0")
            Main.kernel.notify_unicast_changes(subnet)
        elif action == "RTM_NEWLINK" or action == "RTM_DELLINK":
            attrs = msg["attrs"]
            if_name = None
            operation = None
            for (key, value) in attrs:
                print((key, value))
                if key == "IFLA_IFNAME":
                    if_name = value
                elif key == "IFLA_OPERSTATE":
                    operation = value
                if if_name is not None and operation is not None:
                    break
            if if_name is not None:
                print(if_name + ": " + operation)
            UnicastRouting.lock.release()
            if operation == 'DOWN':
                Main.kernel.remove_interface(if_name, membership=True, pim=True)
            subnet = ipaddress.ip_network("0.0.0.0/0")
            Main.kernel.notify_unicast_changes(subnet)
            '''
        else:
            UnicastRouting.lock.release()

    def stop(self):
        """
        No longer monitor unicast changes....
        Invoked whenever the protocol is stopped
        """
        if self._ipdb:
            self._ipdb.release()
        if UnicastRouting.ipdb:
            UnicastRouting.ipdb = None
