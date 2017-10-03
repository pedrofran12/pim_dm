from pyroute2 import IPDB, IPRoute
import socket

#ipdb = IPDB()
ipr = IPRoute()

def get_route(ip_dst: str):
    with IPDB() as ipdb:
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
def get_metric(ip_dst: str):
    unicast_routing_entry = get_route(ip_dst)
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
def check_rpf(ip_dst):
    # obter index da interface
    # rpf_interface_index = ipr.get_routes(family=socket.AF_INET, dst=ip)[0]['attrs'][2][1]
    # interface_name = if_indextoname(rpf_interface_index)
    # return interface_name

    # obter ip da interface de saida
    rpf_interface_source = ipr.get_routes(family=socket.AF_INET, dst=ip_dst)[0]['attrs'][3][1]
    return rpf_interface_source


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


def stop():
    ipr.close()

#ip = input("ip=")
#get_metric(ip)