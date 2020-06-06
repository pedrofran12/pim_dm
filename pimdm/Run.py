#!/usr/bin/env python3

import os
import sys
import socket
import argparse
import traceback
import _pickle as pickle

from pimdm import Main
from pimdm.daemon.Daemon import Daemon

VERSION = "1.1"


def client_socket(data_to_send):
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = '/tmp/pim_uds_socket'
    #print('connecting to %s' % server_address)
    try:
        sock.connect(server_address)
        sock.sendall(pickle.dumps(data_to_send))
        data_rcv = sock.recv(1024 * 256)
        if data_rcv:
            print(pickle.loads(data_rcv))
    except socket.error:
        pass
    finally:
        #print('closing socket')
        sock.close()


class MyDaemon(Daemon):
    def run(self):
        Main.main()
        server_address = '/tmp/pim_uds_socket'

        # Make sure the socket does not already exist
        try:
            os.unlink(server_address)
        except OSError:
            if os.path.exists(server_address):
                raise

        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Bind the socket to the port
        sock.bind(server_address)

        # Listen for incoming connections
        sock.listen(1)
        while True:
            try:
                connection, client_address = sock.accept()
                data = connection.recv(256 * 1024)
                print(sys.stderr, 'sending data back to the client')
                print(pickle.loads(data))
                args = pickle.loads(data)
                if 'ipv4' not in args and 'ipv6' not in args or not (args.ipv4 or args.ipv6):
                    args.ipv4 = True
                    args.ipv6 = False

                if 'list_interfaces' in args and args.list_interfaces:
                    connection.sendall(pickle.dumps(Main.list_enabled_interfaces(ipv4=args.ipv4, ipv6=args.ipv6)))
                elif 'list_neighbors' in args and args.list_neighbors:
                    connection.sendall(pickle.dumps(Main.list_neighbors(ipv4=args.ipv4, ipv6=args.ipv6)))
                elif 'list_state' in args and args.list_state:
                    connection.sendall(pickle.dumps(Main.list_state(ipv4=args.ipv4, ipv6=args.ipv6)))
                elif 'add_interface' in args and args.add_interface:
                    Main.add_pim_interface(args.add_interface[0], False, ipv4=args.ipv4, ipv6=args.ipv6)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'add_interface_sr' in args and args.add_interface_sr:
                    Main.add_pim_interface(args.add_interface_sr[0], True, ipv4=args.ipv4, ipv6=args.ipv6)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'add_interface_igmp' in args and args.add_interface_igmp:
                    Main.add_membership_interface(interface_name=args.add_interface_igmp[0], ipv4=True, ipv6=False)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'add_interface_mld' in args and args.add_interface_mld:
                    Main.add_membership_interface(interface_name=args.add_interface_mld[0], ipv4=False, ipv6=True)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'remove_interface' in args and args.remove_interface:
                    Main.remove_interface(args.remove_interface[0], pim=True, ipv4=args.ipv4, ipv6=args.ipv6)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'remove_interface_igmp' in args and args.remove_interface_igmp:
                    Main.remove_interface(args.remove_interface_igmp[0], membership=True, ipv4=True, ipv6=False)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'remove_interface_mld' in args and args.remove_interface_mld:
                    Main.remove_interface(args.remove_interface_mld[0], membership=True, ipv4=False, ipv6=True)
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'stop' in args and args.stop:
                    Main.stop()
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'test' in args and args.test:
                    Main.test(args.test[0], args.test[1])
                    connection.shutdown(socket.SHUT_RDWR)
            except Exception:
                connection.shutdown(socket.SHUT_RDWR)
                traceback.print_exc()
            finally:
                # Clean up the connection
                connection.close()


def main():
    """
    Entry point for PIM-DM
    """
    parser = argparse.ArgumentParser(description='PIM-DM protocol', prog='pim-dm')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-start", "--start", action="store_true", default=False, help="Start PIM")
    group.add_argument("-stop", "--stop", action="store_true", default=False, help="Stop PIM")
    group.add_argument("-restart", "--restart", action="store_true", default=False, help="Restart PIM")
    group.add_argument("-li", "--list_interfaces", action="store_true", default=False, help="List All PIM Interfaces. "
                                                                                            "Use -4 or -6 to specify IPv4 or IPv6 interfaces.")
    group.add_argument("-ln", "--list_neighbors", action="store_true", default=False, help="List All PIM Neighbors. "
                                                                                           "Use -4 or -6 to specify IPv4 or IPv6 PIM neighbors.")
    group.add_argument("-ls", "--list_state", action="store_true", default=False, help="List IGMP/MLD and PIM-DM state machines."
                                                                                       " Use -4 or -6 to specify IPv4 or IPv6 state respectively.")
    group.add_argument("-mr", "--multicast_routes", action="store_true", default=False, help="List Multicast Routing table. "
                                                                                             "Use -4 or -6 to specify IPv4 or IPv6 multicast routing table.")
    group.add_argument("-ai", "--add_interface", nargs=1, metavar='INTERFACE_NAME', help="Add PIM interface. "
                                                                                         "Use -4 or -6 to specify IPv4 or IPv6 interface.")
    group.add_argument("-aisr", "--add_interface_sr", nargs=1, metavar='INTERFACE_NAME', help="Add PIM interface with State Refresh enabled. "
                                                                                              "Use -4 or -6 to specify IPv4 or IPv6 interface.")
    group.add_argument("-aiigmp", "--add_interface_igmp", nargs=1, metavar='INTERFACE_NAME', help="Add IGMP interface")
    group.add_argument("-aimld", "--add_interface_mld", nargs=1, metavar='INTERFACE_NAME', help="Add MLD interface")
    group.add_argument("-ri", "--remove_interface", nargs=1, metavar='INTERFACE_NAME', help="Remove PIM interface. "
                                                                                            "Use -4 or -6 to specify IPv4 or IPv6 interface.")
    group.add_argument("-riigmp", "--remove_interface_igmp", nargs=1, metavar='INTERFACE_NAME', help="Remove IGMP interface")
    group.add_argument("-rimld", "--remove_interface_mld", nargs=1, metavar='INTERFACE_NAME', help="Remove MLD interface")
    group.add_argument("-v", "--verbose", action="store_true", default=False, help="Verbose (print all debug messages)")
    group.add_argument("-t", "--test", nargs=2, metavar=('ROUTER_NAME', 'SERVER_LOG_IP'), help="Tester... send log information to SERVER_LOG_IP. Set the router name to ROUTER_NAME")
    group.add_argument("--version", action='version', version='%(prog)s ' + VERSION)
    group_ipversion = parser.add_mutually_exclusive_group(required=False)
    group_ipversion.add_argument("-4", "--ipv4", action="store_true", default=False, help="Setting for IPv4")
    group_ipversion.add_argument("-6", "--ipv6", action="store_true", default=False, help="Setting for IPv6")
    args = parser.parse_args()

    #print(parser.parse_args())
    # This script must be run as root!
    if os.geteuid() != 0:
        sys.exit('PIM-DM must be run as root!')

    daemon = MyDaemon('/tmp/Daemon-pim.pid')
    if args.start:
        print("start")
        daemon.start()
        sys.exit(0)
    elif args.stop:
        client_socket(args)
        daemon.stop()
        sys.exit(0)
    elif args.restart:
        daemon.restart()
        sys.exit(0)
    elif args.verbose:
        os.system("tail -f /var/log/pimdm/stdout")
        sys.exit(0)
    elif args.multicast_routes:
        if args.ipv4 or not args.ipv6:
            os.system("ip mroute show")
        elif args.ipv6:
            os.system("ip -6 mroute show")
        sys.exit(0)
    elif not daemon.is_running():
        print("PIM-DM is not running")
        parser.print_usage()
        sys.exit(0)

    client_socket(args)


if __name__ == "__main__":
    main()
