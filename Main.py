import netifaces

from prettytable import PrettyTable

from Interface import Interface
from Neighbor import Neighbor


class Main(object):
    class __Main:
        def __init__(self):
            self.interfaces = {}  # interfaces with multicast routing enabled
            self.neighbors = {}  # multicast router neighbors
            self.protocols = {}

        def add_interface(self, ip):
            if ip not in self.interfaces:
                interface = Interface(ip)
                self.interfaces[ip] = interface
                #self.protocols[0].force_send_handle(interface)  # TODO force send hello packet to added interface

        # TODO: verificar melhor este metodo:
        def remove_interface(self, ip):
            # TODO remover neighbors desta interface
            if ip in self.interfaces:
                for (ip_neighbor, neighbor) in list(self.neighbors.items()):
                    # TODO ver melhor este algoritmo
                    if neighbor.contact_interface == self.interfaces[ip]:
                        self.remove_neighbor(ip_neighbor)
                self.protocols[0].force_send_remove_handle(self.interfaces[ip])
                self.interfaces[ip].remove()
                del self.interfaces[ip]
                print("removido neighbor")

        def add_neighbor(self, contact_interface, ip, random_number, keep_alive_period):
            print("ADD NEIGHBOR")
            if ip not in self.neighbors:
                self.neighbors[ip] = Neighbor(contact_interface, ip, random_number, keep_alive_period)
            print(self.neighbors.keys())

        def get_neighbor(self, ip) -> Neighbor:
            if ip not in self.neighbors:
                return None
            return self.neighbors[ip]

        def remove_neighbor(self, ip):
            if ip in self.neighbors:
                del self.neighbors[ip]

        def add_protocol(self, protocol_number, protocol_obj):
            self.protocols[protocol_number] = protocol_obj

        def list_neighbors(self):
            t = PrettyTable(['Neighbor IP', 'KeepAlive', "Generation ID"])
            for ip, neighbor in list(self.neighbors.items()):
                import socket, struct  # TODO atualmente conversao manual de numero para string ip
                ip = socket.inet_ntoa(struct.pack('!L', ip))
                t.add_row([ip, neighbor.keep_alive_period, neighbor.generation_id])
            print(t)

        def list_enabled_interfaces(self):
            t = PrettyTable(['Interface', 'IP', 'Enabled'])
            for interface in netifaces.interfaces():
                # TODO: fix same interface with multiple ips
                ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                status = ip in self.interfaces
                t.add_row([interface, ip, status])
            print(t)

        def main(self, ip_interfaces_to_add):
            from Hello import Hello
            Hello()

            for ip in ip_interfaces_to_add:
                self.add_interface(ip)

    # MAIN SINGLETON
    instance = None

    def __new__(cls):  # __new__ always a classmethod
        if not Main.instance:
            Main.instance = Main.__Main()
        return Main.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
