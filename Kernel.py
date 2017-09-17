import socket
import struct
import netifaces
import threading
import traceback
from RWLock.RWLock import RWLockWrite
import Main

from tree.root_interface import *
from tree.non_root_interface import *
from tree.KernelEntry import KernelEntry

"""
class KernelEntry:
    def __init__(self, source_ip: str, group_ip: str, inbound_interface_index: int):
        self.source_ip = source_ip
        self.group_ip = group_ip

        # decide inbound interface based on rpf check
        self.inbound_interface_index = Main.kernel.vif_dic[self.check_rpf()]

        # all other interfaces = outbound
        #self.outbound_interfaces = [1] * Kernel.MAXVIFS
        #self.outbound_interfaces[self.inbound_interface_index] = 0

        self._lock = threading.Lock()

        # todo
        self.state = {}  # type: Dict[int, SFRMTreeInterface]
        for i in range(Kernel.MAXVIFS):
            if i == self.inbound_interface_index:
                self.state[i] = SFRMRootInterface(self, i, False)
            else:
                self.state[i] = SFRMNonRootInterface(self, i)

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()

    def get_inbound_interface_index(self):
        return self.inbound_interface_index

    def get_outbound_interfaces_indexes(self):
        # todo check state of outbound interfaces
        outbound_indexes = [0]*Kernel.MAXVIFS
        for (index, state) in self.state.items():
            outbound_indexes[index] = state.is_forwarding()
        return outbound_indexes

    def check_rpf(self):
        from pyroute2 import IPRoute
        # from utils import if_indextoname

        ipr = IPRoute()
        # obter index da interface
        # rpf_interface_index = ipr.get_routes(family=socket.AF_INET, dst=ip)[0]['attrs'][2][1]
        # interface_name = if_indextoname(rpf_interface_index)
        # return interface_name

        # obter ip da interface de saida
        rpf_interface_source = ipr.get_routes(family=socket.AF_INET, dst=socket.inet_ntoa(self.source_ip))[0]['attrs'][3][1]
        return rpf_interface_source

    def recv_data_msg(self, index):
        self.state[index].recv_data_msg()

    def recv_assert_msg(self, index, packet):
        self.state[index].recv_assert_msg(packet, None)

    def recv_prune_msg(self, index, packet):
        self.state[index].recv_prune_msg(None, None)

    def recv_join_msg(self, index, packet):
        self.state[index].recv_join_msg(None, None)



    def change(self):
        # todo: changes on unicast routing or multicast routing...

        Main.kernel.set_multicast_route(self)

    def delete(self):
        Main.kernel.remove_multicast_route(self)

"""

class Kernel:
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


    def __init__(self):
        # Kernel is running
        self.running = True

        # KEY : interface_ip, VALUE : vif_index
        self.vif_dic = {}
        self.vif_index_to_name_dic = {}
        self.vif_name_to_index_dic = {}

        # KEY : (source_ip, group_ip), VALUE : KernelEntry ???? TODO
        self.routing = {}

        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP)

        # MRT INIT
        s.setsockopt(socket.IPPROTO_IP, Kernel.MRT_INIT, 1)

        # MRT PIM
        s.setsockopt(socket.IPPROTO_IP, Kernel.MRT_PIM, 0)

        self.socket = s
        self.rwlock = RWLockWrite()


        # Create virtual interfaces
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            try:
                # ignore localhost interface
                if interface == 'lo':
                    continue
                addrs = netifaces.ifaddresses(interface)
                addr = addrs[netifaces.AF_INET][0]['addr']
                self.create_virtual_interface(ip_interface=addr, interface_name=interface)
            except Exception:
                continue

        # receive signals from kernel with a background thread
        handler_thread = threading.Thread(target=self.handler)
        handler_thread.daemon = True
        handler_thread.start()

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
    def create_virtual_interface(self, ip_interface: str or bytes, interface_name: str, index: int = None, flags=0x0):
        if type(ip_interface) is str:
            ip_interface = socket.inet_aton(ip_interface)

        if index is None:
            index = len(self.vif_dic)
        struct_mrt_add_vif = struct.pack("HBBI 4s 4s", index, flags, 1, 0, ip_interface, socket.inet_aton("0.0.0.0"))
        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_ADD_VIF, struct_mrt_add_vif)
        self.vif_dic[socket.inet_ntoa(ip_interface)] = index
        self.vif_index_to_name_dic[index] = interface_name
        self.vif_name_to_index_dic[interface_name] = index

    def remove_virtual_interface(self, ip_interface):
        index = self.vif_dic[ip_interface]
        struct_vifctl = struct.pack("HBBI 4s 4s", index, 0, 0, 0, socket.inet_aton("0.0.0.0"), socket.inet_aton("0.0.0.0"))

        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_DEL_VIF, struct_vifctl)

        del self.vif_dic[ip_interface]
        del self.vif_name_to_index_dic[self.vif_index_to_name_dic[index]]
        del self.vif_index_to_name_dic[index]
        # TODO alterar MFC's para colocar a 0 esta interface


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
        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_ADD_MFC, struct_mfcctl)

        # TODO: ver melhor tabela routing
        #self.routing[(socket.inet_ntoa(source_ip), socket.inet_ntoa(group_ip))] = {"inbound_interface_index": inbound_interface_index, "outbound_interfaces": outbound_interfaces}

    def flood(self, ip_src, ip_dst, iif):
        source_ip = socket.inet_aton(ip_src)
        group_ip = socket.inet_aton(ip_dst)

        outbound_interfaces = [1]*Kernel.MAXVIFS
        outbound_interfaces[iif] = 0
        outbound_interfaces_and_other_parameters = outbound_interfaces + [0]*4

        #outbound_interfaces, 0, 0, 0, 0 <- only works with python>=3.5
        #struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces, 0, 0, 0, 0)
        struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, iif, *outbound_interfaces_and_other_parameters)
        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_ADD_MFC, struct_mfcctl)

    def remove_multicast_route(self, kernel_entry: KernelEntry):
        source_ip = socket.inet_aton(kernel_entry.source_ip)
        group_ip = socket.inet_aton(kernel_entry.group_ip)
        outbound_interfaces_and_other_parameters = [0] + [0]*Kernel.MAXVIFS + [0]*4

        struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, *outbound_interfaces_and_other_parameters)

        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_DEL_MFC, struct_mfcctl)

    def exit(self):
        self.running = False

        # MRT DONE
        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_DONE, 1)
        self.socket.close()


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
                msg = self.socket.recv(5000)
                print(len(msg))
                (_, _, im_msgtype, im_mbz, im_vif, _, im_src, im_dst) = struct.unpack("II B B B B 4s 4s", msg[:20])
                print(im_msgtype)
                print(im_mbz)
                print(im_vif)
                print(socket.inet_ntoa(im_src))
                print(socket.inet_ntoa(im_dst))
                print(struct.unpack("II B B B B 4s 4s", msg[:20]))
                if im_mbz != 0:
                    continue

                ip_src = socket.inet_ntoa(im_src)
                ip_dst = socket.inet_ntoa(im_dst)

                if im_msgtype == Kernel.IGMPMSG_NOCACHE:
                    print("IGMP NO CACHE")
                    self.igmpmsg_nocache_handler(ip_src, ip_dst, im_vif)
                elif im_msgtype == Kernel.IGMPMSG_WRONGVIF:
                    self.igmpmsg_wrongvif_handler(ip_src, ip_dst, im_vif)
                else:
                    raise Exception
            except Exception:
                traceback.print_exc()
                continue

    # receive multicast (S,G) packet and multicast routing table has no (S,G) entry
    def igmpmsg_nocache_handler(self, ip_src, ip_dst, iif):
        source_group_pair = (ip_src, ip_dst)
        with self.rwlock.genWlock():
            if source_group_pair in self.routing:
                return

            kernel_entry = KernelEntry(ip_src, ip_dst, iif)
            self.routing[(ip_src, ip_dst)] = kernel_entry
            self.set_multicast_route(kernel_entry)

    # receive multicast (S,G) packet in a outbound_interface
    def igmpmsg_wrongvif_handler(self, ip_src, ip_dst, iif):
        #kernel_entry = self.routing[(ip_src, ip_dst)]
        kernel_entry = self.get_routing_entry((ip_src, ip_dst))
        kernel_entry.recv_data_msg(iif)

    def get_routing_entry(self, source_group: tuple):
        with self.rwlock.genRlock():
            return self.routing[source_group]
