#!/usr/bin/env python3

import os
import sys
import time
import glob
import socket
import argparse
import threading
import traceback
import _pickle as pickle
from prettytable import PrettyTable

from pimdm import Main
from pimdm.tree import pim_globals
from pimdm.daemon.Daemon import Daemon

VERSION = "1.3.5"


def client_socket(data_to_send, print_output=True):
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = pim_globals.DAEMON_SOCKET.format(pim_globals.MULTICAST_TABLE_ID)
    #print('connecting to %s' % server_address)
    try:
        sock.connect(server_address)
        sock.sendall(pickle.dumps(data_to_send))
        data_rcv = sock.recv(1024 * 256)
        if data_rcv:
            if print_output:
                print(pickle.loads(data_rcv))
            else:
                return pickle.loads(data_rcv)
    except socket.error:
        pass
    finally:
        #print('closing socket')
        sock.close()


class MyDaemon(Daemon):
    def run(self):
        Main.main()
        server_address = pim_globals.DAEMON_SOCKET.format(pim_globals.MULTICAST_TABLE_ID)

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
                elif 'list_instances' in args and args.list_instances:
                    connection.sendall(pickle.dumps(Main.list_instances()))
                elif 'stop' in args and args.stop:
                    Main.stop()
                    connection.shutdown(socket.SHUT_RDWR)
                    break
                elif 'test' in args and args.test:
                    Main.test(args.test[0], args.test[1])
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'config' in args and args.config:
                    Main.set_config(args.config[0])
                    connection.shutdown(socket.SHUT_RDWR)
                elif 'get_config' in args and args.get_config:
                    connection.sendall(pickle.dumps(Main.get_config()))
                elif 'drop' in args and args.drop:
                    Main.drop(args.drop[0], int(args.drop[1]))
            except Exception:
                connection.shutdown(socket.SHUT_RDWR)
                traceback.print_exc()
            finally:
                # Clean up the connection
                connection.close()
        sock.close()


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
    group.add_argument("-instances", "--list_instances", action="store_true", default=False,
                       help="List running PIM-DM daemon processes.")
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
    group.add_argument("-config", "--config", nargs=1, metavar='CONFIG_FILE_PATH', type=str,
                       help="File path for configuration file.")
    group.add_argument("-get_config", "--get_config", action="store_true", default=False,
                       help="Get configuration file of live daemon.")
    #group.add_argument("-drop", "--drop", nargs=2, metavar=('INTERFACE_NAME', 'PACKET_TYPE'), type=str)
    group.add_argument("--version", action='version', version='%(prog)s ' + VERSION)
    group_ipversion = parser.add_mutually_exclusive_group(required=False)
    group_ipversion.add_argument("-4", "--ipv4", action="store_true", default=False, help="Setting for IPv4")
    group_ipversion.add_argument("-6", "--ipv6", action="store_true", default=False, help="Setting for IPv6")
    group_vrf = parser.add_argument_group()
    group_vrf.add_argument("-mvrf", "--multicast_vrf", nargs=1, default=[pim_globals.MULTICAST_TABLE_ID],
                           metavar='MULTICAST_VRF_NUMBER', type=int,
                           help="Define multicast table id. This can be used on -start to explicitly start the daemon"
                                " process on a given vrf. It can also be used with the other commands "
                                "(for example add, list, ...) for setting/getting information on a given daemon"
                                " process")
    group_vrf.add_argument("-uvrf", "--unicast_vrf", nargs=1, default=[pim_globals.UNICAST_TABLE_ID],
                           metavar='UNICAST_VRF_NUMBER', type=int,
                           help="Define unicast table id for getting unicast information (RPF checks, RPC costs, ...). "
                                "This information can only be defined at startup with -start command")
    args = parser.parse_args()

    #print(parser.parse_args())
    # This script must be run as root!
    if os.geteuid() != 0:
        sys.exit('PIM-DM must be run as root!')

    if args.list_instances:
        pid_files = glob.glob("/tmp/Daemon-pim*.pid")
        t = PrettyTable(['Instance PID', 'Multicast VRF', 'Unicast VRF'])

        for pid_file in pid_files:
            d = MyDaemon(pid_file)
            pim_globals.MULTICAST_TABLE_ID = pid_file[15:-4]
            if not d.is_running():
                continue

            t_new = client_socket(args, print_output=False)
            t.add_row(t_new.split("|"))
        print(t)
        return

    pim_globals.MULTICAST_TABLE_ID = args.multicast_vrf[0]
    pim_globals.UNICAST_TABLE_ID = args.unicast_vrf[0]

    daemon = MyDaemon(pim_globals.DAEMON_PROCESS_FILE.format(pim_globals.MULTICAST_TABLE_ID))
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
    elif args.config:
        try:
            from pimdm import Config
            args.config[0] = os.path.abspath(args.config[0])
            [pim_globals.MULTICAST_TABLE_ID, pim_globals.UNICAST_TABLE_ID] = Config.get_vrfs(args.config[0])
            daemon = MyDaemon(pim_globals.DAEMON_PROCESS_FILE.format(pim_globals.MULTICAST_TABLE_ID))

            if not daemon.is_running():
                x = threading.Thread(target=daemon.start, args=())
                x.start()
                x.join()

            while not daemon.is_running():
                time.sleep(1)
        except ModuleNotFoundError:
            print("PYYAML needs to be installed. Execute \"pip3 install pyyaml\"")
            sys.exit(0)
        except ImportError:
            print("PYYAML needs to be installed. Execute \"pip3 install pyyaml\"")
            sys.exit(0)
    elif args.verbose:
        os.system("tail -f {}".format(pim_globals.DAEMON_LOG_STDOUT_FILE.format(pim_globals.MULTICAST_TABLE_ID)))
        sys.exit(0)
    elif args.multicast_routes:
        if args.ipv4 or not args.ipv6:
            os.system("ip mroute show table " + str(pim_globals.MULTICAST_TABLE_ID))
        elif args.ipv6:
            os.system("ip -6 mroute show table " + str(pim_globals.MULTICAST_TABLE_ID))
        sys.exit(0)
    elif not daemon.is_running():
        print("PIM-DM is not running")
        parser.print_usage()
        sys.exit(0)

    client_socket(args)


if __name__ == "__main__":
    main()
