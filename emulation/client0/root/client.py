import socket
import struct
import sys
import argparse
import netifaces
import signal
import sys

is_running = True
sock = None

def exit(signal, frame):
    global is_running
    is_running = False
    sock.close()
    sys.exit(0)

def chooseInterface():
    interfaces = netifaces.interfaces()
    def printInterfaces():
        print('Indique a interface de captura:')
        for i in range(len(interfaces)):
            print (i+1, '-', interfaces[i])
        
    if len(interfaces) == 1: #user has just 1 interface and any
        return interfaces[0]
    else:
        printInterfaces()
        inputValue = input('Numero da interface: ')

        if int(inputValue)-1 not in range(len(interfaces)):
            raise Exception('numero de interface invalida')
        inputValue = interfaces[int(inputValue)-1]
        return inputValue

if not hasattr(socket, 'SO_BINDTODEVICE'):
    socket.SO_BINDTODEVICE = 25

signal.signal(signal.SIGINT, exit)
signal.signal(signal.SIGTERM, exit)


server_address = ('', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def main(interface_name, multicast_group):
    # Bind to the server address
    sock.bind(server_address)

    ip_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']

    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                    socket.inet_aton(multicast_group) + socket.inet_aton(ip_interface))

    # Receive/respond loop
    while is_running:
        data, address = sock.recvfrom(10240)
        print(data.decode("utf-8"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multicast receiver')
    parser.add_argument("-i", "--interface", nargs=1, metavar='INTERFACE_NAME',
                       help="Set receiver interface")
    parser.add_argument("-g", "--group", nargs=1, metavar='MULTICAST_GROUP_IP',
                       help="Set multicast group to receive traffic")
    args = parser.parse_args()

    if args.interface:
        interface_name = args.interface[0]
    else:
        interface_name = chooseInterface()

    if args.group:
        multicast_group = args.group[0]
    else:
        multicast_group = '224.12.12.12'

    main(interface_name, multicast_group)
