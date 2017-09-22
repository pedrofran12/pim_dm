import socket
import struct
import sys
#import trac
import traceback

#message = 'very important data'
multicast_group = ('224.12.12.12', 10000)

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set a timeout so the socket does not block indefinitely when trying
# to receive data.
#sock.settimeout(0.2)

# Set the time-to-live for messages to 1 so they do not go past the
# local network segment.
ttl = struct.pack('b', 12)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:

    # Send data to the multicast group
    #print >>sys.stderr, 'sending "%s"' % message
    #sent = sock.sendto(message, multicast_group)

    # Look for responses from all recipients
    while True:
        #print >>sys.stderr, 'waiting to receive'
        input_msg = input('msg --> ')
        try:
            #message = struct.pack("s", input_msg.encode('utf-8'))
            msg = bytes(input_msg, "utf-8")
            sock.sendto(msg, multicast_group)

        except:
            traceback.print_exc()
            continue
            #print >>sys.stderr, 'received "%s" from %s' % (data, server)

finally:
    #print >>sys.stderr, 'closing socket'
    sock.close()
