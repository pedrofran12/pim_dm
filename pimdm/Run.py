#!/usr/bin/env python3

import argparse, glob, os, signal, socket, sys, traceback
import _pickle as pickle
from prettytable import PrettyTable

from pimdm import Main
from pimdm.tree import pim_globals
from pimdm.utils import exit


VERSION = "1.4.0"
PROCESS_DIRECTORY = '/var/run/pim-dm'
PROCESS_SOCKET = os.path.join(PROCESS_DIRECTORY, 'pim_uds_socket{}')
PROCESS_LOG_FOLDER = '/var/log/pimdm'
PROCESS_LOG_STDOUT_FILE = os.path.join(PROCESS_LOG_FOLDER, 'stdout{}')
PROCESS_LOG_STDERR_FILE = os.path.join(PROCESS_LOG_FOLDER, 'stderror{}')

def clean_process_dir():
    os.remove(process_file_path())
    os.remove(process_socket_path())
    if not os.listdir(PROCESS_DIRECTORY):
        os.rmdir(PROCESS_DIRECTORY)

def client_socket(data_to_send, print_output=True):
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = PROCESS_SOCKET.format(pim_globals.MULTICAST_TABLE_ID)
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

def is_running():
    return os.path.exists(process_file_path())

def main_loop(sock):
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
                connection.shutdown(socket.SHUT_RDWR)
                break                
            elif 'test' in args and args.test:
                Main.test(args.test[0], args.test[1])
                connection.shutdown(socket.SHUT_RDWR)
            elif 'get_config' in args and args.get_config:
                connection.sendall(pickle.dumps(Main.get_config()))
            elif 'drop' in args and args.drop:
                Main.drop(args.drop[0], int(args.drop[1]))
        except Exception as e:
            connection.sendall(pickle.dumps(e))
            connection.shutdown(socket.SHUT_RDWR)
            traceback.print_exc()
        finally:
            # Clean up the connection
            if 'connection' in locals():
                connection.close()

def args_parser():
    parser = argparse.ArgumentParser(description='PIM-DM protocol', prog='pim-dm')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-start", "--start", action="store_true", default=False, help="Start PIM")
    group.add_argument("-stop", "--stop", action="store_true", default=False, help="Stop PIM")
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
    return parser

def list_instances(args):
    t = PrettyTable(['Instance PID', 'Multicast VRF', 'Unicast VRF'])

    for multicast_table_id in glob.glob(os.path.join(PROCESS_DIRECTORY, '*')):
        pim_globals.MULTICAST_TABLE_ID = multicast_table_id

        t_new = client_socket(args, print_output=False)
        t.add_row(t_new.split("|"))
    print(t)

def run_config(conf_file_path):
    try:
        from pimdm import Config
        pim_globals.MULTICAST_TABLE_ID, pim_globals.UNICAST_TABLE_ID = Config.get_vrfs(conf_file_path)
        start(conf_file_path)
    except (ImportError, ModuleNotFoundError):
        raise Exception("PYYAML needs to be installed. Execute \"pip3 install pyyaml\"")

def print_multicast_routes(args):
    if args.ipv4 or not args.ipv6:
        os.system("ip mroute show table " + str(pim_globals.MULTICAST_TABLE_ID))
    elif args.ipv6:
        os.system("ip -6 mroute show table " + str(pim_globals.MULTICAST_TABLE_ID))

def main():
    """
    Entry point for PIM-DM
    """
    parser = args_parser()
    args = parser.parse_args()

    # This script must be run as root!
    if os.geteuid() != 0:
        sys.exit('PIM-DM must be run as root!')

    if args.list_instances:
        list_instances(args)
        return

    pim_globals.MULTICAST_TABLE_ID = args.multicast_vrf[0]
    pim_globals.UNICAST_TABLE_ID = args.unicast_vrf[0]

    if args.start:
        start()
    elif args.stop:
        client_socket(args)
    elif args.config:
        run_config(os.path.abspath(args.config[0]))
    elif args.verbose:
        os.system("tail -f {}".format(PROCESS_LOG_STDOUT_FILE.format(pim_globals.MULTICAST_TABLE_ID)))
    elif args.multicast_routes:
        print_multicast_routes(args)
    elif not is_running():
        print("PIM-DM is not running")
        parser.print_usage()

    client_socket(args)

def process_file_path():
    return os.path.join(PROCESS_DIRECTORY, str(pim_globals.MULTICAST_TABLE_ID))

def process_socket_path():
    return PROCESS_SOCKET.format(pim_globals.MULTICAST_TABLE_ID)

def get_server_address():
    server_address = process_socket_path()

    # Make sure the socket does not already exist
    if os.path.exists(server_address):
        raise Exception(server_address + ' already exists !')
    return server_address

def exit_main(cleanup):
    exit.acquire(0)
    while cleanup:
        try:
            cleanup.pop()()
        except Exception:
            traceback.print_exc()
    exit.release()

def start(conf_file_path=None):
    exit.signal(0, signal.SIGINT, signal.SIGTERM)

    process_file = process_file_path()
    if is_running():
        sys.stderr.write(process_file + ' exists. Process already running ?\n')
        sys.exit(1)

    cleanup = [clean_process_dir]
    try:
        os.makedirs(PROCESS_DIRECTORY, exist_ok=True)
        os.mknod(process_file)

        os.makedirs(PROCESS_LOG_FOLDER, exist_ok=True)
        os.chdir(PROCESS_LOG_FOLDER)
        os.umask(0)

        # redirect standard file descriptors

        sys.stdout.flush()
        sys.stderr.flush()
        so = open(PROCESS_LOG_STDOUT_FILE.format(pim_globals.MULTICAST_TABLE_ID), 'a+')
        cleanup.append(so.close)
        se = open(PROCESS_LOG_STDERR_FILE.format(pim_globals.MULTICAST_TABLE_ID), 'a+')
        cleanup.append(se.close)

        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        print("start")
        cleanup.insert(0, Main.stop)
        Main.main()
        if conf_file_path:
            Main.set_config(conf_file_path)

        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        cleanup.insert(0, sock.close)

        # Bind the socket to the port
        sock.bind(get_server_address())

        # Listen for incoming connections
        sock.listen(1)

        main_loop(sock)
    finally:
        exit_main(cleanup)

if __name__ == "__main__":
    main()
