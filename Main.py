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
                #self.protocols[0].force_send_handle(interface)  # force send hello packet to added interface

        # TODO: verificar melhor este metodo:
        def remove_interface(self, ip):
            self.protocols[0].force_send_remove_handle(self.interfaces[ip])
            del self.interfaces[ip]

        def add_neighbor(self, contact_interface, ip, random_number, keep_alive_period):
            print("ADD NEIGHBOR")
            if ip not in self.neighbors:
                self.neighbors[ip] = Neighbor(contact_interface, ip, random_number, keep_alive_period)
            print(self.neighbors.keys())

        def get_neighbor(self, ip):
            if ip not in self.neighbors:
                return None
            return self.neighbors[ip]

        def remove_neighbor(self, ip):
            if ip in self.neighbors:
                del self.neighbors[ip]

        def add_protocol(self, protocol_number, protocol_obj):
            self.protocols[protocol_number] = protocol_obj

        def list_neighbors(self):
            t = PrettyTable(['Neighbor IP', 'KeepAlive', "Random Number"])
            for ip, neighbor in self.neighbors.items():
                t.add_row([ip, neighbor.keep_alive_period, neighbor.random_number])
            print(t)

        def list_enabled_interfaces(self):
            t = PrettyTable(['Interface', 'IP', 'Status'])
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
