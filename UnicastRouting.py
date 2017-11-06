from queue import Queue
from threading import Thread

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
        self.event_queue = Queue(maxsize=0)


        UnicastRouting.ipr = IPRoute()
        UnicastRouting.ipdb = IPDB()
        self._ipdb = UnicastRouting.ipdb
        self._ipdb.register_callback(UnicastRouting.unicast_changes)
        #self.working = True
        #self.worker_thread = Thread(target=self.worker)
        #self.worker_thread.daemon = True
        #self.worker_thread.start()


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
        return (entry_protocol, entry_cost)

    """
    def get_rpf(ip_dst: str):
        unicast_routing_entry = get_route(ip_dst)
        #interface_oif = unicast_routing_entry['oif']
        if not unicast_routing_entry['multipath']:
            interface_oif = unicast_routing_entry['oif']
        else:
            multiple_entries = unicast_routing_entry['multipath']
            print(multiple_entries)
            (entry0, _) = multiple_entries
            print(entry0)
            interface_oif = entry0['oif']
    
        print("ola")
        print(ipdb.interfaces[interface_oif]['ipaddr'])
    
        for i in range(len(ipdb.interfaces[interface_oif]['ipaddr'])):
            print("ola2")
            interface = ipdb.interfaces[interface_oif]['ipaddr'][i]
            print(interface)
            if interface['family'] == socket.AF_INET:
                return interface['address']
        return None
    """

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
        #unicast_event = QueueItem(ipdb, msg, action)
        #self.event_queue.put(unicast_event)
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
            #Main.kernel.notify_unicast_changes(subnet)
        elif action == "RTM_NEWADDR" or action == "RTM_DELADDR":
            print("a")

    '''
    def worker(self):
        global ipdb
        while self.working:
            item = self.event_queue.get()
            ipdb = item.ipdb
            if item.action == "RTM_NEWROUTE" or item.action == "RTM_DELROUTE":
                mask_len = item.action["dst_len"]
                network_address = None
                attrs = item.action["attrs"]
                for (key, value) in attrs:
                    if key == "RTA_DST":
                        network_address = value
                        break
                subnet = ipaddress.ip_network(network_address + "/" + mask_len)
                Main.kernel.notify_kernel_about_unicast_change(subnet)
            elif item.action == "RTM_NEWADDR" or item.action == "RTM_DELADDR":
                print("a")
    '''


            #print(ipdb)
            #print(msg)
            #print(action)






    """
    def get_metric(ip_dst: str):
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
        print("metric=", info["priority"])
        print("proto=", info["proto"])
        #print(info.keys())
        #if info["gateway"]:
        #    print("next_hop=", info["gateway"])
        #elif info["prefsrc"]:
        #    print("next_hop=", info["prefsrc"])
        return (info["proto"], info["priority"])
    
    
    def check_rpf(ip_dst: str):
        from pyroute2 import IPRoute
        # from utils import if_indextoname
    
        ipr = IPRoute()
        # obter index da interface
        # rpf_interface_index = ipr.get_routes(family=socket.AF_INET, dst=ip)[0]['attrs'][2][1]
        # interface_name = if_indextoname(rpf_interface_index)
        # return interface_name
    
        # obter ip da interface de saida
        rpf_interface_source = ipr.get_routes(family=socket.AF_INET, dst=ip_dst)[0]['attrs'][3][1]
        return rpf_interface_source
    """


    def stop(self):
        #self.working = False

        if UnicastRouting.ipr:
            UnicastRouting.ipr.close()
        if UnicastRouting.ipdb:
            UnicastRouting.ipdb = None
        if self._ipdb:
            self._ipdb.release()


        #ip = input("ip=")
    #get_metric(ip)

'''
class QueueItem(object):
    def __init__(self, ipdb, msg, action):
        self.ipdb = ipdb
        self.msg = msg
        self.action = action
'''
