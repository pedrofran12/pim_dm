import netifaces
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
    t = PrettyTable(['Neighbor IP', 'KeepAlive', "Generation ID"])
    for ip, neighbor in list(neighbors.items()):
        import socket, struct  # TODO atualmente conversao manual de numero para string ip
        ip = socket.inet_ntoa(struct.pack('!L', ip))
        t.add_row([ip, neighbor.keep_alive_period, neighbor.generation_id])
    print(t)
    return str(t)

def list_enabled_interfaces():
    global interfaces
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
