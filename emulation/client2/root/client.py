import socket
import struct
import sys
import netifaces


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

multicast_group = '224.12.12.12'
server_address = ('', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

#interface_name = input("interface name: ")
interface_name = chooseInterface()
ip_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']


# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                     socket.inet_aton(multicast_group) + socket.inet_aton(ip_interface))

#sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface_name + "\0").encode('utf-8'))


# Receive/respond loop
while True:
    #print >>sys.stderr, '\nwaiting to receive message'
    data, address = sock.recvfrom(10240)
    print(data.decode("utf-8"))

    #print >>sys.stderr, 'received %s bytes from %s' % (len(data), address)
    #print >>sys.stderr, data

    #print >>sys.stderr, 'sending acknowledgement to', address
    #sock.sendto('ack', address)
