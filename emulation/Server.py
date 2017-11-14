import rpyc
import socket
import _pickle as pickle
from argparse import Namespace
import os

class MyService(rpyc.Service):
    daemon = None


    def client_socket(self, data_to_send):
        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = './uds_socket'
        # print('connecting to %s' % server_address)
        try:
            sock.connect(server_address)
            sock.sendall(pickle.dumps(data_to_send))
            data_rcv = sock.recv(1024 * 256)
            if data_rcv:
                return pickle.loads(data_rcv)
        except socket.error as error:
            print(error)
            pass
        finally:
            # print('closing socket')
            sock.close()


    def on_connect(self):
        # code that runs when a connection is created
        # (to init the serivce, if needed)
        os.system("python3 Run.py -restart")
        pass

    def on_disconnect(self):
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_kill(self):
        import signal
        with open("/tmp/Daemon-pim.pid", 'r') as pf:
            pid = int(pf.read().strip())
        os.kill(pid, signal.SIGTERM)


    def exposed_add_interface(self, interface_name):
        self.client_socket(Namespace(add_interface_igmp=[interface_name]))
        self.client_socket(Namespace(add_interface=[interface_name]))

    def exposed_remove_interface(self, interface_name):
        self.client_socket(Namespace(remove_interface_igmp=[interface_name]))
        self.client_socket(Namespace(remove_interface=[interface_name]))

    def exposed_get_neighbors(self): # this is an exposed method
        import re
        table_list_neighbors = self.client_socket(Namespace(list_neighbors=True))
        #x = table_list_neighbors.replace("-", "").replace("+", "").replace("\n", "").replace(" ", "").split("|")
        x = re.sub(r"[\s\-\+]+", "", table_list_neighbors).split("|")

        x = list(filter(lambda a: a != '', x))
        dict = {}

        for i in range(5, len(x), 5):
            print(x[i+1])
            if x[i] not in dict:
                dict[x[i]] = {x[i+1]: [x[i+2], x[i+3], x[i+4]]}
            else:
                dict[x[i]][x[i+1]] = [x[i+2], x[i+3], x[i+4]]
        return (table_list_neighbors, dict)

    def exposed_list_igm_state(self): # this is an exposed method
        x = self.client_socket(Namespace(list_state=True))
        x = x.split("Multicast Routing State:")[0]
        x = x.replace(" - ", "No")
        x = x.replace("-", "").replace("+", "").replace("\n", "").replace(" ", "").split("|")
        x = list(filter(lambda a: a != '', x))

        for i in range(0, len(x), 4):
            print(x[i+1])

    def exposed_list_state(self): # this is an exposed method
        x = self.client_socket(Namespace(list_state=True))
        x = x.split("Multicast Routing State:")[1]
        x = x.replace(" - ", "No")
        x = x.replace("-", "").replace("+", "").replace("\n", "").replace(" ", "").split("|")
        x = list(filter(lambda a: a != '', x))

        for i in range(0, len(x), 7):
            print(x[i+1])




    def get_question(self):  # while this method is not exposed
        return "what is the airspeed velocity of an unladen swallow?"


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(MyService, port = 10000)
    t.start()