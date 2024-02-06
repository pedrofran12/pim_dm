import os
import socket
import struct
import ipaddress
import logging
from socket import if_nametoindex
from threading import RLock, Thread
from abc import abstractmethod, ABCMeta

from pimdm import UnicastRouting, Main
from pimdm.rwlock.RWLock import RWLockWrite
from pimdm.tree import pim_globals

from mld.InterfaceMLD import InterfaceMLD
from igmp.InterfaceIGMP import InterfaceIGMP
from pimdm.InterfacePIM import InterfacePim
from pimdm.InterfacePIM6 import InterfacePim6
from pimdm.tree.KernelEntry import KernelEntry
from pimdm.tree.KernelEntryInterface import KernelEntry4Interface, KernelEntry6Interface


class Kernel(metaclass=ABCMeta):
    # Max Number of Virtual Interfaces
    MAXVIFS = 32

    def __init__(self, kernel_socket):
        # Kernel is running
        self.running = True

        # KEY : interface_ip, VALUE : vif_index
        self.vif_index_to_name_dic = {}  # KEY : vif_index, VALUE : interface_name
        self.vif_name_to_index_dic = {}  # KEY : interface_name, VALUE : vif_index

        # KEY : source_ip, VALUE : {group_ip: KernelEntry}
        self.routing = {}

        self.socket = kernel_socket
        self.rwlock = RWLockWrite()
        self.interface_lock = RLock()

        # Create register interface
        # todo useless in PIM-DM... useful in PIM-SM
        #self.create_virtual_interface("0.0.0.0", "pimreg", index=0, flags=Kernel.VIFF_REGISTER)

        # interfaces being monitored by this process
        self.pim_interface = {}  # name: interface_pim
        self.membership_interface = {}  # name: interface_igmp or interface_mld

        # logs
        self.interface_logger = logging.LoggerAdapter(
          logging.getLogger('pim.KernelInterface'),
          {'tree': None, 'vif': None, 'interfacename': None, 'routername': None},
        )
        self.tree_logger = logging.getLogger('pim.KernelTree')

        # receive signals from kernel with a background thread
        self.handler_thread = Thread(target=self.handler)
        self.handler_thread.daemon = True
        self.handler_thread.start()

    '''
    Structure to create/remove virtual interfaces
    struct vifctl {
        vifi_t	vifc_vifi;		        /* Index of VIF */
        unsigned char vifc_flags;	    /* VIFF_ flags */
        unsigned char vifc_threshold;	/* ttl limit */
        unsigned int vifc_rate_limit;	/* Rate limiter values (NI) */
        union {
            struct in_addr vifc_lcl_addr;     /* Local interface address */
            int            vifc_lcl_ifindex;  /* Local interface index   */
        };
        struct in_addr vifc_rmt_addr;	/* IPIP tunnel addr */
    };
    '''
    @abstractmethod
    def create_virtual_interface(self, ip_interface: str or bytes, interface_name: str, index, flags=0x0):
        raise NotImplementedError

    def create_pim_interface(self, interface_name: str, state_refresh_capable:bool):
        with self.interface_lock:
            pim_interface = self.pim_interface.get(interface_name)
            membership_interface = self.membership_interface.get(interface_name)
            vif_already_exists = pim_interface or membership_interface
            if pim_interface:
                # already exists
                pim_interface.set_state_refresh_capable(state_refresh_capable)
                return
            elif membership_interface:
                index = membership_interface.vif_index
            else:
                index = (range(0, self.MAXVIFS) - self.vif_index_to_name_dic.keys()).pop()

            ip_interface = None
            if interface_name not in self.pim_interface:
                pim_interface = self._create_pim_interface_object(interface_name, index, state_refresh_capable)
                self.pim_interface[interface_name] = pim_interface
                ip_interface = pim_interface.ip_interface

            if not vif_already_exists:
                self.create_virtual_interface(ip_interface=ip_interface, interface_name=interface_name, index=index)

    @abstractmethod
    def _create_pim_interface_object(self, interface_name, index, state_refresh_capable):
        raise NotImplementedError

    def create_membership_interface(self, interface_name: str):
        with self.interface_lock:
            pim_interface = self.pim_interface.get(interface_name)
            membership_interface = self.membership_interface.get(interface_name)
            vif_already_exists = pim_interface or membership_interface
            if membership_interface:
                # already exists
                return
            elif pim_interface:
                index = pim_interface.vif_index
            else:
                index = (range(0, self.MAXVIFS) - self.vif_index_to_name_dic.keys()).pop()

            if interface_name not in self.membership_interface:
                membership_interface = self._create_membership_interface_object(interface_name, index)
                self.membership_interface[interface_name] = membership_interface
                ip_interface = membership_interface.ip_interface

                if not vif_already_exists:
                    self.create_virtual_interface(ip_interface=ip_interface, interface_name=interface_name, index=index)
                membership_interface.enable()

    @abstractmethod
    def _create_membership_interface_object(self, interface_name, index):
        raise NotImplementedError

    def remove_interface(self, interface_name, membership: bool = False, pim: bool = False):
        with self.interface_lock:
            if pim and interface_name in self.pim_interface:
                self.pim_interface.pop(interface_name).remove()
            if membership and interface_name in self.membership_interface:
                self.membership_interface.pop(interface_name).remove()

            if ((pim and not interface_name in self.membership_interface) or
                (membership and not interface_name in self.pim_interface)):
                self.remove_virtual_interface(interface_name)

    @abstractmethod
    def remove_virtual_interface(self, interface_name):
        raise NotImplementedError

    def start_forwarding(self, index):
        for new_interface in (kernel_entry.new_interface
            for source_dict in self.routing.values()
            for kernel_entry in source_dict.values()
        ):
            new_interface(index)


    def stop_forwarding(self, index):
        # change MFC's to not forward traffic by this interface (set OIL to 0 for this interface)
        with self.rwlock.genWlock():
            for remove_interface in (kernel_entry.remove_interface
                    for source_dict in self.routing.values()
                    for kernel_entry in source_dict.values()
            ):
                remove_interface(index)

        interface_name = self.vif_index_to_name_dic.pop(index) 
        self.interface_logger.debug('Remove virtual interface: %s -> %d', interface_name, index)

    #############################################
    # Manipulate multicast routing table
    #############################################
    @abstractmethod
    def set_multicast_route(self, kernel_entry: KernelEntry):
        raise NotImplementedError

    @abstractmethod
    def set_flood_multicast_route(self, source_ip, group_ip, inbound_interface_index):
        raise NotImplementedError

    @abstractmethod
    def remove_multicast_route(self, kernel_entry: KernelEntry):
        raise NotImplementedError

    @abstractmethod
    def close_socket(self):
        raise NotImplementedError

    def exit(self):
        self.running = False
        self.close_socket()
        self.handler_thread.join()

    @abstractmethod
    def handler(self):
        raise NotImplementedError

    def get_routing_entry(self, source_group: tuple, create_if_not_existent=True):
        ip_src = source_group[0]
        ip_dst = source_group[1]
        with self.rwlock.genRlock():
            if ip_src in self.routing and ip_dst in self.routing[ip_src]:
                return self.routing[ip_src][ip_dst]

        with self.rwlock.genWlock():
            if ip_src in self.routing and ip_dst in self.routing[ip_src]:
                return self.routing[ip_src][ip_dst]
            elif create_if_not_existent:
                kernel_entry = KernelEntry(ip_src, ip_dst, self._get_kernel_entry_interface())
                if ip_src not in self.routing:
                    self.routing[ip_src] = {}

                iif = UnicastRouting.check_rpf(ip_src)
                self.set_flood_multicast_route(ip_src, ip_dst, iif)
                self.routing[ip_src][ip_dst] = kernel_entry
                return kernel_entry
            else:
                return None

    @staticmethod
    @abstractmethod
    def _get_kernel_entry_interface():
        pass

    # notify KernelEntries about changes at the unicast routing table
    def notify_unicast_changes(self, subnet):
        with self.rwlock.genWlock():
            for network_update in (kernel_entry.network_update
                    for kernel_entry in group_ip_dict
                    for source_ip, group_ip_dict in self.routing.items()
                    if ipaddress.ip_address(source_ip) in subnet
            ):
                network_update()


    # notify about changes at the interface (IP)
    '''
    def notify_interface_change(self, interface_name):
        with self.interface_lock:
            # check if interface was already added
            if interface_name not in self.vif_name_to_index_dic:
                return

            print("trying to change ip")
            pim_interface = self.pim_interface.get(interface_name)
            if pim_interface:
                old_ip = pim_interface.get_ip()
                pim_interface.change_interface()
                new_ip = pim_interface.get_ip()
                if old_ip != new_ip:
                    self.vif_dic[new_ip] = self.vif_dic.pop(old_ip)

            igmp_interface = self.igmp_interface.get(interface_name)
            if igmp_interface:
                igmp_interface.change_interface()
    '''

    # When interface changes number of neighbors verify if olist changes and prune/forward respectively
    def interface_change_number_of_neighbors(self):
        with self.rwlock.genRlock():
            for groups_dict in self.routing.values():
                for entry in groups_dict.values():
                    entry.change_at_number_of_neighbors()

    # When new neighbor connects try to resend last state refresh msg (if AssertWinner)
    def new_or_reset_neighbor(self, vif_index, neighbor_ip):
        with self.rwlock.genRlock():
            for groups_dict in self.routing.values():
                for entry in groups_dict.values():
                    entry.new_or_reset_neighbor(vif_index, neighbor_ip)


class Kernel4(Kernel):
    # MRT
    MRT_BASE    = 200
    MRT_INIT    = (MRT_BASE)      # /* Activate the kernel mroute code 	*/
    MRT_DONE    = (MRT_BASE + 1)  # /* Shutdown the kernel mroute		*/
    MRT_ADD_VIF = (MRT_BASE + 2)  # /* Add a virtual interface		    */
    MRT_DEL_VIF = (MRT_BASE + 3)  # /* Delete a virtual interface		*/
    MRT_ADD_MFC = (MRT_BASE + 4)  # /* Add a multicast forwarding entry	*/
    MRT_DEL_MFC = (MRT_BASE + 5)  # /* Delete a multicast forwarding entry	*/
    MRT_VERSION = (MRT_BASE + 6)  # /* Get the kernel multicast version	*/
    MRT_ASSERT  = (MRT_BASE + 7)  # /* Activate PIM assert mode		    */
    MRT_PIM     = (MRT_BASE + 8)  # /* enable PIM code			        */
    MRT_TABLE   = (MRT_BASE + 9)  # /* Specify mroute table ID		    */
    #MRT_ADD_MFC_PROXY = (MRT_BASE + 10)  # /* Add a (*,*|G) mfc entry	*/
    #MRT_DEL_MFC_PROXY = (MRT_BASE + 11)  # /* Del a (*,*|G) mfc entry	*/
    #MRT_MAX = (MRT_BASE + 11)

    # Max Number of Virtual Interfaces
    MAXVIFS = 32

    # SIGNAL MSG TYPE
    IGMPMSG_NOCACHE = 1
    IGMPMSG_WRONGVIF = 2
    IGMPMSG_WHOLEPKT = 3  # NOT USED ON PIM-DM

    # Interface flags
    VIFF_TUNNEL      = 0x1  # IPIP tunnel
    VIFF_SRCRT       = 0x2  # NI
    VIFF_REGISTER    = 0x4  # register vif
    VIFF_USE_IFINDEX = 0x8  # use vifc_lcl_ifindex instead of vifc_lcl_addr to find an interface

    def __init__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP)

        # MRT TABLE
        if pim_globals.MULTICAST_TABLE_ID != 0:
            try:
                s.setsockopt(socket.IPPROTO_IP, self.MRT_TABLE, pim_globals.MULTICAST_TABLE_ID)
            except Exception as e:
                logging.error(e, exc_info=True)

        # MRT INIT
        s.setsockopt(socket.IPPROTO_IP, self.MRT_INIT, 1)

        # MRT PIM
        s.setsockopt(socket.IPPROTO_IP, self.MRT_PIM, 0)
        s.setsockopt(socket.IPPROTO_IP, self.MRT_ASSERT, 1)

        super().__init__(s)

    '''
    Structure to create/remove virtual interfaces
    struct vifctl {
        vifi_t	vifc_vifi;		        /* Index of VIF */
        unsigned char vifc_flags;	    /* VIFF_ flags */
        unsigned char vifc_threshold;	/* ttl limit */
        unsigned int vifc_rate_limit;	/* Rate limiter values (NI) */
        union {
            struct in_addr vifc_lcl_addr;     /* Local interface address */
            int            vifc_lcl_ifindex;  /* Local interface index   */
        };
        struct in_addr vifc_rmt_addr;	/* IPIP tunnel addr */
    };
    '''
    def create_virtual_interface(self, ip_interface: str or bytes, interface_name: str, index, flags=0x0):
        if type(ip_interface) is str:
            ip_interface = socket.inet_aton(ip_interface)

        struct_mrt_add_vif = struct.pack("HBBI 4s 4s", index, flags, 1, 0, ip_interface,
                                         socket.inet_aton("0.0.0.0"))
        os.system("ip mrule del iif {}".format(interface_name))
        os.system("ip mrule del oif {}".format(interface_name))
        if pim_globals.MULTICAST_TABLE_ID != 0:
            os.system("ip mrule add iif {} lookup {}".format(interface_name, pim_globals.MULTICAST_TABLE_ID))
            os.system("ip mrule add oif {} lookup {}".format(interface_name, pim_globals.MULTICAST_TABLE_ID))
        with self.rwlock.genWlock():
            self.socket.setsockopt(socket.IPPROTO_IP, self.MRT_ADD_VIF, struct_mrt_add_vif)
            self.vif_index_to_name_dic[index] = interface_name
            self.vif_name_to_index_dic[interface_name] = index

            self.start_forwarding(index)

        self.interface_logger.debug('Create virtual interface: %s -> %d', interface_name, index)
        return index

    def remove_virtual_interface(self, interface_name):
        #with self.interface_lock:
        if interface_name in self.vif_name_to_index_dic:
            index = self.vif_name_to_index_dic.pop(interface_name)
            struct_vifctl = struct.pack("HBBI 4s 4s", index, 0, 0, 0, socket.inet_aton("0.0.0.0"), socket.inet_aton("0.0.0.0"))

            os.system("ip mrule del iif {}".format(interface_name))
            os.system("ip mrule del oif {}".format(interface_name))
            self.socket.setsockopt(socket.IPPROTO_IP, self.MRT_DEL_VIF, struct_vifctl)

            self.stop_forwarding(index)


    '''
    /* Cache manipulation structures for mrouted and PIMd */
    struct mfcctl {
        struct in_addr mfcc_origin;		    /* Origin of mcast	*/
        struct in_addr mfcc_mcastgrp;		/* Group in question	*/
        vifi_t mfcc_parent; 			    /* Where it arrived	*/
        unsigned char mfcc_ttls[MAXVIFS];	/* Where it is going	*/
        unsigned int mfcc_pkt_cnt;		    /* pkt count for src-grp */
        unsigned int mfcc_byte_cnt;
        unsigned int mfcc_wrong_if;
        int mfcc_expire;
    };
    '''
    def set_multicast_route(self, kernel_entry: KernelEntry):
        source_ip = socket.inet_aton(kernel_entry.source_ip)
        group_ip = socket.inet_aton(kernel_entry.group_ip)

        outbound_interfaces = kernel_entry.get_outbound_interfaces_indexes()
        if len(outbound_interfaces) != Kernel.MAXVIFS:
            raise Exception

        #outbound_interfaces_and_other_parameters = list(kernel_entry.outbound_interfaces) + [0]*4
        outbound_interfaces_and_other_parameters = outbound_interfaces + [0]*4

        #outbound_interfaces, 0, 0, 0, 0 <- only works with python>=3.5
        #struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces, 0, 0, 0, 0)
        struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, kernel_entry.inbound_interface_index, *outbound_interfaces_and_other_parameters)
        self.socket.setsockopt(socket.IPPROTO_IP, self.MRT_ADD_MFC, struct_mfcctl)

    def set_flood_multicast_route(self, source_ip, group_ip, inbound_interface_index):
        source_ip = socket.inet_aton(source_ip)
        group_ip = socket.inet_aton(group_ip)

        outbound_interfaces = [1]*self.MAXVIFS
        outbound_interfaces[inbound_interface_index] = 0

        #outbound_interfaces_and_other_parameters = list(kernel_entry.outbound_interfaces) + [0]*4
        outbound_interfaces_and_other_parameters = outbound_interfaces + [0]*3 + [20]

        #outbound_interfaces, 0, 0, 0, 0 <- only works with python>=3.5
        #struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces, 0, 0, 0, 0)
        struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces_and_other_parameters)
        self.socket.setsockopt(socket.IPPROTO_IP, self.MRT_ADD_MFC, struct_mfcctl)

    def remove_multicast_route(self, kernel_entry: KernelEntry):
        source_ip = socket.inet_aton(kernel_entry.source_ip)
        group_ip = socket.inet_aton(kernel_entry.group_ip)
        outbound_interfaces_and_other_parameters = [0] + [0]*Kernel.MAXVIFS + [0]*4

        struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, *outbound_interfaces_and_other_parameters)
        self.socket.setsockopt(socket.IPPROTO_IP, self.MRT_DEL_MFC, struct_mfcctl)
        self.routing[kernel_entry.source_ip].pop(kernel_entry.group_ip)
        if len(self.routing[kernel_entry.source_ip]) == 0:
            self.routing.pop(kernel_entry.source_ip)

    def close_socket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP) as s:
            s.sendto(b'', ('', 0))
        self.socket.close()

    def exit(self):
        # MRT DONE
        self.socket.setsockopt(socket.IPPROTO_IP, self.MRT_DONE, 1)
        super().exit()


    '''
    /* This is the format the mroute daemon expects to see IGMP control
    * data. Magically happens to be like an IP packet as per the original
    */
    struct igmpmsg {
        __u32 unused1,unused2;
        unsigned char im_msgtype;		/* What is this */
        unsigned char im_mbz;			/* Must be zero */
        unsigned char im_vif;			/* Interface (this ought to be a vifi_t!) */
        unsigned char unused3;
        struct in_addr im_src,im_dst;
    };
    '''
    def handler(self):
        while self.running:
            try:
                msg = self.socket.recv(20)
                (_, _, im_msgtype, im_mbz, im_vif, _, im_src, im_dst) = struct.unpack("II B B B B 4s 4s", msg[:20])
                logging.debug((im_msgtype, im_mbz, socket.inet_ntoa(im_src), socket.inet_ntoa(im_dst)))

                if im_mbz != 0:
                    continue

                logging.debug(im_msgtype)
                logging.debug(im_mbz)
                logging.debug(im_vif)
                logging.debug(socket.inet_ntoa(im_src))
                logging.debug(socket.inet_ntoa(im_dst))
                #print((im_msgtype, im_mbz, socket.inet_ntoa(im_src), socket.inet_ntoa(im_dst)))

                ip_src = socket.inet_ntoa(im_src)
                ip_dst = socket.inet_ntoa(im_dst)

                if im_msgtype == self.IGMPMSG_NOCACHE:
                    logging.debug("IGMP NO CACHE")
                    self.igmpmsg_nocache_handler(ip_src, ip_dst, im_vif)
                elif im_msgtype == self.IGMPMSG_WRONGVIF:
                    logging.debug("WRONG VIF HANDLER")
                    self.igmpmsg_wrongvif_handler(ip_src, ip_dst, im_vif)
                #elif im_msgtype == Kernel.IGMPMSG_WHOLEPKT:
                #    print("IGMP_WHOLEPKT")
                #    self.igmpmsg_wholepacket_handler(ip_src, ip_dst)
                else:
                    raise Exception
            except Exception as e:
                logging.error(e, exc_info=True)

    # receive multicast (S,G) packet and multicast routing table has no (S,G) entry
    def igmpmsg_nocache_handler(self, ip_src, ip_dst, iif):
        source_group_pair = (ip_src, ip_dst)
        self.get_routing_entry(source_group_pair, create_if_not_existent=True).recv_data_msg(iif)

    # receive multicast (S,G) packet in a outbound_interface
    def igmpmsg_wrongvif_handler(self, ip_src, ip_dst, iif):
        source_group_pair = (ip_src, ip_dst)
        self.get_routing_entry(source_group_pair, create_if_not_existent=True).recv_data_msg(iif)


    ''' useless in PIM-DM... useful in PIM-SM
    def igmpmsg_wholepacket_handler(self, ip_src, ip_dst):
        #kernel_entry = self.routing[(ip_src, ip_dst)]
        source_group_pair = (ip_src, ip_dst)
        self.get_routing_entry(source_group_pair, create_if_not_existent=True).recv_data_msg()
        #kernel_entry.recv_data_msg(iif)
    '''

    @staticmethod
    def _get_kernel_entry_interface():
        return KernelEntry4Interface

    def _create_pim_interface_object(self, interface_name, index, state_refresh_capable):
        return InterfacePim(interface_name, index, state_refresh_capable)

    def _create_membership_interface_object(self, interface_name, index):
        return InterfaceIGMP(interface_name, index)


class Kernel6(Kernel):
    # MRT6
    MRT6_BASE = 200
    MRT6_INIT = (MRT6_BASE)                 # /* Activate the kernel mroute code 	*/
    MRT6_DONE = (MRT6_BASE + 1)             # /* Shutdown the kernel mroute		*/
    MRT6_ADD_MIF = (MRT6_BASE + 2)          # /* Add a virtual interface		*/
    MRT6_DEL_MIF = (MRT6_BASE + 3)          # /* Delete a virtual interface		*/
    MRT6_ADD_MFC = (MRT6_BASE + 4)          # /* Add a multicast forwarding entry	*/
    MRT6_DEL_MFC = (MRT6_BASE + 5)          # /* Delete a multicast forwarding entry	*/
    MRT6_VERSION = (MRT6_BASE + 6)          # /* Get the kernel multicast version	*/
    MRT6_ASSERT = (MRT6_BASE + 7)           # /* Activate PIM assert mode		*/
    MRT6_PIM = (MRT6_BASE + 8)              # /* enable PIM code			*/
    MRT6_TABLE = (MRT6_BASE + 9)            # /* Specify mroute table ID		*/
    MRT6_ADD_MFC_PROXY = (MRT6_BASE + 10)   # /* Add a (*,*|G) mfc entry	*/
    MRT6_DEL_MFC_PROXY = (MRT6_BASE + 11)   # /* Del a (*,*|G) mfc entry	*/
    MRT6_MAX = (MRT6_BASE + 11)

    # define SIOCGETMIFCNT_IN6	SIOCPROTOPRIVATE	/* IP protocol privates */
    # define SIOCGETSGCNT_IN6	(SIOCPROTOPRIVATE+1)
    # define SIOCGETRPF	(SIOCPROTOPRIVATE+2)

    # Max Number of Virtual Interfaces
    MAXVIFS = 32

    # SIGNAL MSG TYPE
    MRT6MSG_NOCACHE = 1
    MRT6MSG_WRONGMIF = 2
    MRT6MSG_WHOLEPKT = 3  # /* used for use level encap */

    # Interface flags
    MIFF_REGISTER = 0x1  # /* register vif	*/

    def __init__(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)

        # MRT TABLE
        if pim_globals.MULTICAST_TABLE_ID != 0:
            try:
                s.setsockopt(socket.IPPROTO_IPV6, self.MRT6_TABLE, pim_globals.MULTICAST_TABLE_ID)
            except Exception as e:
                logging.error(e, exc_info=True)

        # MRT INIT
        s.setsockopt(socket.IPPROTO_IPV6, self.MRT6_INIT, 1)

        # MRT PIM
        s.setsockopt(socket.IPPROTO_IPV6, self.MRT6_PIM, 0)
        s.setsockopt(socket.IPPROTO_IPV6, self.MRT6_ASSERT, 1)

        super().__init__(s)

    '''
    Structure to create/remove multicast interfaces
    struct mif6ctl {
        mifi_t	mif6c_mifi;		        /* Index of MIF */
        unsigned char mif6c_flags;	    /* MIFF_ flags */
        unsigned char vifc_threshold;	/* ttl limit */
        __u16	 mif6c_pifi;		    /* the index of the physical IF */
        unsigned int vifc_rate_limit;	/* Rate limiter values (NI) */
    };
    '''
    def create_virtual_interface(self, ip_interface, interface_name: str, index, flags=0x0):
        physical_if_index = if_nametoindex(interface_name)
        struct_mrt_add_vif = struct.pack("HBBHI", index, flags, 1, physical_if_index, 0)

        os.system("ip -6 mrule del iif {}".format(interface_name))
        os.system("ip -6 mrule del oif {}".format(interface_name))
        if pim_globals.MULTICAST_TABLE_ID != 0:
            os.system("ip -6 mrule add iif {} lookup {}".format(interface_name, pim_globals.MULTICAST_TABLE_ID))
            os.system("ip -6 mrule add oif {} lookup {}".format(interface_name, pim_globals.MULTICAST_TABLE_ID))

        with self.rwlock.genWlock():
            self.socket.setsockopt(socket.IPPROTO_IPV6, self.MRT6_ADD_MIF, struct_mrt_add_vif)
            self.vif_index_to_name_dic[index] = interface_name
            self.vif_name_to_index_dic[interface_name] = index

            self.start_forwarding(index)

        self.interface_logger.debug('Create virtual interface: %s -> %d', interface_name, index)
        return index

    def remove_virtual_interface(self, interface_name):
        # with self.interface_lock:
        if interface_name in self.vif_name_to_index_dic:
            mif_index = self.vif_name_to_index_dic.pop(interface_name)
            physical_if_index = if_nametoindex(interface_name)

            struct_vifctl = struct.pack("HBBHI", mif_index, 0, 0, physical_if_index, 0)
            self.socket.setsockopt(socket.IPPROTO_IPV6, self.MRT6_DEL_MIF, struct_vifctl)

            os.system("ip -6 mrule del iif {}".format(interface_name))
            os.system("ip -6 mrule del oif {}".format(interface_name))

            self.stop_forwarding(mif_index)

    '''
    /* Cache manipulation structures for mrouted and PIMd */
    typedef	__u32 if_mask;
    typedef struct if_set {
        if_mask ifs_bits[__KERNEL_DIV_ROUND_UP(IF_SETSIZE, NIFBITS)];
    } if_set;

    struct mf6cctl {
        struct sockaddr_in6 mf6cc_origin;		/* Origin of mcast	*/
        struct sockaddr_in6 mf6cc_mcastgrp;		/* Group in question	*/
        mifi_t	mf6cc_parent;			        /* Where it arrived	*/
        struct if_set mf6cc_ifset;		        /* Where it is going */
    };
    '''
    def set_multicast_route(self, kernel_entry: KernelEntry):
        source_ip = socket.inet_pton(socket.AF_INET6, kernel_entry.source_ip)
        sockaddr_in6_source = struct.pack("H H I 16s I", socket.AF_INET6, 0, 0, source_ip, 0)
        group_ip = socket.inet_pton(socket.AF_INET6, kernel_entry.group_ip)
        sockaddr_in6_group = struct.pack("H H I 16s I", socket.AF_INET6, 0, 0, group_ip, 0)

        outbound_interfaces = kernel_entry.get_outbound_interfaces_indexes()
        if len(outbound_interfaces) != 8:
            raise Exception

        # outbound_interfaces_and_other_parameters = list(kernel_entry.outbound_interfaces) + [0]*4
        # outbound_interfaces_and_other_parameters = outbound_interfaces + [0]*4
        outgoing_interface_list = outbound_interfaces

        # outbound_interfaces, 0, 0, 0, 0 <- only works with python>=3.5
        # struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces, 0, 0, 0, 0)
        struct_mf6cctl = struct.pack("28s 28s H " + "I" * 8, sockaddr_in6_source, sockaddr_in6_group,
                                     kernel_entry.inbound_interface_index,
                                     *outgoing_interface_list)
        self.socket.setsockopt(socket.IPPROTO_IPV6, self.MRT6_ADD_MFC, struct_mf6cctl)

    def set_flood_multicast_route(self, source_ip, group_ip, inbound_interface_index):
        source_ip = socket.inet_pton(socket.AF_INET6, source_ip)
        sockaddr_in6_source = struct.pack("H H I 16s I", socket.AF_INET6, 0, 0, source_ip, 0)
        group_ip = socket.inet_pton(socket.AF_INET6, group_ip)
        sockaddr_in6_group = struct.pack("H H I 16s I", socket.AF_INET6, 0, 0, group_ip, 0)

        outbound_interfaces = [255] * 8
        outbound_interfaces[inbound_interface_index // 32] = 0xFFFFFFFF & ~(1 << (inbound_interface_index % 32))

        # outbound_interfaces, 0, 0, 0, 0 <- only works with python>=3.5
        # struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces, 0, 0, 0, 0)
        # struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces_and_other_parameters)
        struct_mf6cctl = struct.pack("28s 28s H " + "I" * 8, sockaddr_in6_source, sockaddr_in6_group,
                                     inbound_interface_index, *outbound_interfaces)
        self.socket.setsockopt(socket.IPPROTO_IPV6, self.MRT6_ADD_MFC, struct_mf6cctl)

    def remove_multicast_route(self, kernel_entry: KernelEntry):
        source_ip = socket.inet_pton(socket.AF_INET6, kernel_entry.source_ip)
        sockaddr_in6_source = struct.pack("H H I 16s I", socket.AF_INET6, 0, 0, source_ip, 0)
        group_ip = socket.inet_pton(socket.AF_INET6, kernel_entry.group_ip)
        sockaddr_in6_group = struct.pack("H H I 16s I", socket.AF_INET6, 0, 0, group_ip, 0)
        outbound_interfaces = [0] * 8

        # struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, *outbound_interfaces_and_other_parameters)
        struct_mf6cctl = struct.pack("28s 28s H " + "I" * 8, sockaddr_in6_source, sockaddr_in6_group, 0,
                                     *outbound_interfaces)

        self.socket.setsockopt(socket.IPPROTO_IPV6, self.MRT6_DEL_MFC, struct_mf6cctl)
        self.routing[kernel_entry.source_ip].pop(kernel_entry.group_ip)
        if len(self.routing[kernel_entry.source_ip]) == 0:
            self.routing.pop(kernel_entry.source_ip)

    def close_socket(self):
        with socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6) as s:
            s.sendto(b'0000', ('', 0))
        self.socket.close()

    def exit(self):
        # MRT DONE
        self.socket.setsockopt(socket.IPPROTO_IPV6, self.MRT6_DONE, 1)
        super().exit()

    '''
    /*
     * Structure used to communicate from kernel to multicast router.
     * We'll overlay the structure onto an MLD header (not an IPv6 heder like igmpmsg{}
     * used for IPv4 implementation). This is because this structure will be passed via an
     * IPv6 raw socket, on which an application will only receiver the payload i.e the data after
     * the IPv6 header and all the extension headers. (See section 3 of RFC 3542)
     */

    struct mrt6msg {
        __u8		im6_mbz;		/* must be zero		   */
        __u8		im6_msgtype;	/* what type of message    */
        __u16		im6_mif;		/* mif rec'd on		   */
        __u32		im6_pad;		/* padding for 64 bit arch */
        struct in6_addr	im6_src, im6_dst;
    };

    /* ip6mr netlink cache report attributes */
    enum {
        IP6MRA_CREPORT_UNSPEC,
        IP6MRA_CREPORT_MSGTYPE,
        IP6MRA_CREPORT_MIF_ID,
        IP6MRA_CREPORT_SRC_ADDR,
        IP6MRA_CREPORT_DST_ADDR,
        IP6MRA_CREPORT_PKT,
        __IP6MRA_CREPORT_MAX
    };
    '''
    def handler(self):
        while self.running:
            try:
                msg = self.socket.recv(500)
                if len(msg) < 40:
                    continue
                (im6_mbz, im6_msgtype, im6_mif, _, im6_src, im6_dst) = struct.unpack("B B H I 16s 16s", msg[:40])
                # print((im_msgtype, im_mbz, socket.inet_ntoa(im_src), socket.inet_ntoa(im_dst)))

                if im6_mbz != 0:
                    continue

                logging.debug(im6_mbz)
                logging.debug(im6_msgtype)
                logging.debug(im6_mif)
                logging.debug(socket.inet_ntop(socket.AF_INET6, im6_src))
                logging.debug(socket.inet_ntop(socket.AF_INET6, im6_dst))
                # print((im_msgtype, im_mbz, socket.inet_ntoa(im_src), socket.inet_ntoa(im_dst)))

                ip_src = socket.inet_ntop(socket.AF_INET6, im6_src)
                ip_dst = socket.inet_ntop(socket.AF_INET6, im6_dst)

                if im6_msgtype == self.MRT6MSG_NOCACHE:
                    logging.debug("MRT6 NO CACHE")
                    self.msg_nocache_handler(ip_src, ip_dst, im6_mif)
                elif im6_msgtype == self.MRT6MSG_WRONGMIF:
                    logging.debug("WRONG MIF HANDLER")
                    self.msg_wrongvif_handler(ip_src, ip_dst, im6_mif)
                # elif im_msgtype == Kernel.IGMPMSG_WHOLEPKT:
                #    print("IGMP_WHOLEPKT")
                #    self.igmpmsg_wholepacket_handler(ip_src, ip_dst)
                else:
                    raise Exception
            except Exception as e:
                logging.error(e, exc_info=True)

    # receive multicast (S,G) packet and multicast routing table has no (S,G) entry
    def msg_nocache_handler(self, ip_src, ip_dst, iif):
        source_group_pair = (ip_src, ip_dst)
        self.get_routing_entry(source_group_pair, create_if_not_existent=True).recv_data_msg(iif)

    # receive multicast (S,G) packet in a outbound_interface
    def msg_wrongvif_handler(self, ip_src, ip_dst, iif):
        source_group_pair = (ip_src, ip_dst)
        self.get_routing_entry(source_group_pair, create_if_not_existent=True).recv_data_msg(iif)

    ''' useless in PIM-DM... useful in PIM-SM
    def msg_wholepacket_handler(self, ip_src, ip_dst):
        #kernel_entry = self.routing[(ip_src, ip_dst)]
        source_group_pair = (ip_src, ip_dst)
        self.get_routing_entry(source_group_pair, create_if_not_existent=True).recv_data_msg()
        #kernel_entry.recv_data_msg(iif)
    '''

    @staticmethod
    def _get_kernel_entry_interface():
        return KernelEntry6Interface

    def _create_pim_interface_object(self, interface_name, index, state_refresh_capable):
        return InterfacePim6(interface_name, index, state_refresh_capable)

    def _create_membership_interface_object(self, interface_name, index):
        return InterfaceMLD(interface_name, index)
