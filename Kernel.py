import socket
import struct
import netifaces
import threading

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
    IGMPMSG_WHOLEPKT = 3


    def __init__(self):
        # Kernel is running
        self.running = True

        # KEY : interface_ip, VALUE : vif_index
        self.vif_dic = {}

        # KEY : (source_ip, group_ip), VALUE : ???? TODO
        self.routing = {}

        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP)

        # MRT INIT
        s.setsockopt(socket.IPPROTO_IP, Kernel.MRT_INIT, 1)

        # MRT PIM
        s.setsockopt(socket.IPPROTO_IP, Kernel.MRT_PIM, 1)

        self.socket = s

        # Create virtual interfaces
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            #ignore localhost interface
            if interface == 'lo':
                continue
            addrs = netifaces.ifaddresses(interface)
            addr = addrs[netifaces.AF_INET][0]['addr']
            try:
                self.create_virtual_interface(addr)
            except Exception:
                continue

        #self.set_multicast_route("10.2.2.2", "224.12.12.112", 0)
        # TODO: background thread for receiving signals

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
    def create_virtual_interface(self, ip_interface, index=None, flags=0x0):
        if (type(ip_interface) is not bytes) and (type(ip_interface) is not str):
            raise Exception
        elif type(ip_interface) is str:
            ip_interface = socket.inet_aton(ip_interface)

        if index is None:
            index = len(self.vif_dic)
        struct_mrt_add_vif = struct.pack("HBBI 4s 4s", index, flags, 1, 0, ip_interface, socket.inet_aton("0.0.0.0"))
        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_ADD_VIF, struct_mrt_add_vif)
        self.vif_dic[socket.inet_ntoa(ip_interface)] = index

    def remove_virtual_interface(self, ip_interface):
        index = self.vif_dic[ip_interface]
        return




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
    def set_multicast_route(self, source_ip, group_ip, inbound_interface_index, outbound_interfaces=None):
        if (type(source_ip) not in (bytes, str)) or (type(group_ip) not in (bytes, str)):
            raise Exception
        if type(source_ip) is str:
            source_ip = socket.inet_aton(source_ip)
        if type(group_ip) is str:
            group_ip = socket.inet_aton(group_ip)

        if outbound_interfaces is None:
            outbound_interfaces = [1]*Kernel.MAXVIFS
            outbound_interfaces[inbound_interface_index] = 0
        elif len(outbound_interfaces) != Kernel.MAXVIFS:
            raise Exception

        outbound_interfaces_and_other_parameters = list(outbound_interfaces) + [0]*4
        #outbound_interfaces, 0, 0, 0, 0 <- only works with python>=3.5
        #struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces, 0, 0, 0, 0)
        struct_mfcctl = struct.pack("4s 4s H " + "B"*Kernel.MAXVIFS + " IIIi", source_ip, group_ip, inbound_interface_index, *outbound_interfaces_and_other_parameters)
        self.socket.setsockopt(socket.IPPROTO_IP, Kernel.MRT_ADD_MFC, struct_mfcctl)

        # TODO: ver melhor tabela routing
        self.routing[(socket.inet_ntoa(source_ip), socket.inet_ntoa(group_ip))] = {"inbound_interface_index":inbound_interface_index, "outbound_interfaces": outbound_interfaces}

    def remove_multicast_route(self):
        return

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
                (_, _, im_msgtype, im_mbz, im_vif, _, im_src, im_dst, _) = struct.unpack("II B B B B 4s 4s    8s", msg)
                print(im_msgtype)
                print(im_mbz)
                print(im_vif)
                print(socket.inet_ntoa(im_src))
                print(socket.inet_ntoa(im_dst))
                print(struct.unpack("II B B B B 4s 4s 8s", msg))
                if im_mbz != 0:
                    continue
                if im_msgtype == Kernel.IGMPMSG_NOCACHE:
                    print("IGMP NO CACHE")
                    self.set_multicast_route(im_src, im_dst, im_vif)
                # TODO: handler
            except Exception:
                continue
