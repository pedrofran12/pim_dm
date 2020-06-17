import socket
import struct
import sys
import netifaces
import signal
import sys
import ctypes
import ctypes.util

is_running = True
sock = None
LIBC = ctypes.CDLL(ctypes.util.find_library('c'))

def exit(signal, frame):
    is_running = False
    sock.close()
    sys.exit(0)

def if_nametoindex(name):
    if isinstance(name, str):
        name = name.encode('utf-8')
    elif not isinstance(name, bytes):
         raise TypeError("Require unicode/bytes type for name")
    ret = LIBC.if_nametoindex(name)
    if not ret:
        raise RuntimeError("Invalid Name")
    return ret

def chooseInterface():
    interfaces = netifaces.interfaces()
    def printInterfaces():
        print('Capture interface:')
        for i in range(len(interfaces)):
            print (i+1, '-', interfaces[i])
        
    if len(interfaces) == 1: #user has just 1 interface and any
        return interfaces[0]
    else:
        printInterfaces()
        inputValue = input('Interface number: ')

        if int(inputValue)-1 not in range(len(interfaces)):
            raise Exception('Invalid interface number')
        inputValue = interfaces[int(inputValue)-1]
        return inputValue

if not hasattr(socket, 'SO_BINDTODEVICE'):
    socket.SO_BINDTODEVICE = 25

signal.signal(signal.SIGINT, exit)
signal.signal(signal.SIGTERM, exit)


multicast_group = 'ff05::12:12:12'
server_address = ('', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

#interface_name = input("interface name: ")
interface_name = chooseInterface()


# Tell the operating system to add the socket to the multicast group
# on all interfaces.
if_index = if_nametoindex(interface_name)
sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, socket.inet_pton(socket.AF_INET6, multicast_group) + struct.pack('@I', if_index))
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface_name + "\0").encode('utf-8'))


# Receive/respond loop
while is_running:
    #print >>sys.stderr, '\nwaiting to receive message'
    data, address = sock.recvfrom(10240)
    print(data.decode("utf-8"))

    #print >>sys.stderr, 'received %s bytes from %s' % (len(data), address)
    #print >>sys.stderr, data

    #print >>sys.stderr, 'sending acknowledgement to', address
    #sock.sendto('ack', address)
