from pyroute2 import IPDB, IPRoute
import socket
import RWLock
import Main
import ipaddress


def get_route(ip_dst: str):
    return UnicastRouting.get_route(ip_dst)

def get_metric(ip_dst: str):
    return UnicastRouting.get_metric(ip_dst)

def check_rpf(ip_dst):
    return UnicastRouting.check_rpf(ip_dst)


class UnicastRouting(object):
    ipr = None
    ipdb = None

    def __init__(self):
        UnicastRouting.ipr = IPRoute()
        UnicastRouting.ipdb = IPDB()
        self._ipdb = UnicastRouting.ipdb
        self._ipdb.register_callback(UnicastRouting.unicast_changes)


    @staticmethod
    def get_route(ip_dst: str):
        ipdb = UnicastRouting.ipdb

        ip_bytes = socket.inet_aton(ip_dst)
        ip_int = int.from_bytes(ip_bytes, byteorder='big')
        info = None
        for mask_len in range(32, 0, -1):
            ip_bytes = (ip_int & (0xFFFFFFFF << (32 - mask_len))).to_bytes(4, "big")
            ip_dst = socket.inet_ntoa(ip_bytes) + "/" + str(mask_len)
            print(ip_dst)
            try:
                info = ipdb.routes[ip_dst]
                break
            except:
                continue
        if not info:
            print("0.0.0.0/0")
            info = ipdb.routes["default"]
        print(info)
        return info


    # get metrics (routing preference and cost) to IP ip_dst
    @staticmethod
    def get_metric(ip_dst: str):
        unicast_routing_entry = UnicastRouting.get_route(ip_dst)
        entry_protocol = unicast_routing_entry["proto"]
        entry_cost = unicast_routing_entry["priority"]
        mask = unicast_routing_entry["dst_len"]
        if entry_cost is None:
            entry_cost = 0
        return (entry_protocol, entry_cost, mask)


    # get output interface IP, used to send data to IP ip_dst
    # (root interface IP to ip_dst)
    @staticmethod
    def check_rpf(ip_dst):
        # obter index da interface
        # rpf_interface_index = ipr.get_routes(family=socket.AF_INET, dst=ip)[0]['attrs'][2][1]
        # interface_name = if_indextoname(rpf_interface_index)
        # return interface_name

        # obter ip da interface de saida
        rpf_interface_source = UnicastRouting.ipr.get_routes(family=socket.AF_INET, dst=ip_dst)[0]['attrs'][3][1]
        return rpf_interface_source


    @staticmethod
    def unicast_changes(ipdb, msg, action):
        print("unicast change?")
        print(action)
        UnicastRouting.ipdb = ipdb
        if action == "RTM_NEWROUTE" or action == "RTM_DELROUTE":
            print(ipdb.routes)
            mask_len = msg["dst_len"]
            network_address = None
            attrs = msg["attrs"]
            print(attrs)
            for (key, value) in attrs:
                print((key,value))
                if key == "RTA_DST":
                    network_address = value
                    break
            if network_address is None:
                network_address = "0.0.0.0"
            print(network_address)
            print(mask_len)
            print(network_address + "/" + str(mask_len))
            subnet = ipaddress.ip_network(network_address + "/" + str(mask_len))
            print(str(subnet))
            Main.kernel.notify_unicast_changes(subnet)
        elif action == "RTM_NEWADDR" or action == "RTM_DELADDR":
            # TODO ALTERACOES NA INTERFACE
            '''
            print(msg)
            attrs = msg["attrs"]
            for (key, value) in attrs:
                print((key, value))
                if key == "IFA_LABEL":
                    interface_name = value
                    break
            pim_interface = Main.kernel.pim_interface.get(interface_name)
            pim_interface.change_interface()
            igmp_interface = Main.kernel.igmp_interface.get(interface_name)
            '''
            pass


    def stop(self):
        if UnicastRouting.ipr:
            UnicastRouting.ipr.close()
        if UnicastRouting.ipdb:
            UnicastRouting.ipdb = None
        if self._ipdb:
            self._ipdb.release()
