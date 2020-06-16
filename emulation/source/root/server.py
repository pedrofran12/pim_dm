import socket
import struct
import sys
import netifaces
import traceback
import signal
import argparse
import time

is_running = True
sock = None

def exit(signal, frame):
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


signal.signal(signal.SIGINT, exit)
signal.signal(signal.SIGTERM, exit)

multicast_group = ('224.12.12.12', 10000)

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set the time-to-live for messages to 1 so they do not go past the
# local network segment.
ttl = struct.pack('b', 12)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


def main(interface_name, auto):
    ip_interface = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']

    sock.bind((ip_interface, 10000))
    i = 0
    try:
        # Look for responses from all recipients
        while is_running:
            if auto:
                input_msg = str(i)
                print("msg --> : " + str(input_msg))
                i += 1
                time.sleep(1)
            else:
                input_msg = input('msg --> ')

            try:
                sock.sendto(input_msg.encode("utf-8"), multicast_group)
            except:
                traceback.print_exc()
                continue
                #print >>sys.stderr, 'received "%s" from %s' % (data, server)

    finally:
        #print >>sys.stderr, 'closing socket'
        sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multicast source')
    parser.add_argument("-i", "--interface", nargs=1, metavar='INTERFACE_NAME',
                       help="Set source interface")
    parser.add_argument("-a", "--auto", action="store_true", default=False, help="Automatically send data packets")
    args = parser.parse_args()

    if args.interface:
        interface_name = args.interface[0]
    else:
        interface_name = chooseInterface()
    main(interface_name, args.auto)
