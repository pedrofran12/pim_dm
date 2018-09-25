import socket
import time
import struct
# ficheiros importantes: /usr/include/linux/mroute.h

MRT_BASE    = 200
MRT_INIT    = (MRT_BASE)	# Activate the kernel mroute code 	*/
MRT_DONE	= (MRT_BASE+1)	#/* Shutdown the kernel mroute		*/
MRT_ADD_VIF	= (MRT_BASE+2)	#/* Add a virtual interface		*/
MRT_DEL_VIF	= (MRT_BASE+3)	#/* Delete a virtual interface		*/
MRT_ADD_MFC	= (MRT_BASE+4)	#/* Add a multicast forwarding entry	*/
MRT_DEL_MFC	= (MRT_BASE+5)	#/* Delete a multicast forwarding entry	*/
MRT_VERSION	= (MRT_BASE+6)	#/* Get the kernel multicast version	*/
MRT_ASSERT	= (MRT_BASE+7)	#/* Activate PIM assert mode		*/
MRT_PIM		= (MRT_BASE+8)	#/* enable PIM code			*/
MRT_TABLE	= (MRT_BASE+9)	#/* Specify mroute table ID		*/
MRT_ADD_MFC_PROXY	= (MRT_BASE+10)	#/* Add a (*,*|G) mfc entry	*/
MRT_DEL_MFC_PROXY	= (MRT_BASE+11)	#/* Del a (*,*|G) mfc entry	*/
MRT_MAX		= (MRT_BASE+11)

IGMPMSG_NOCACHE = 1
IGMPMSG_WRONGVIF = 2
IGMPMSG_WHOLEPKT = 3


s2 = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IGMP)

#MRT INIT
s2.setsockopt(socket.IPPROTO_IP, MRT_INIT, 1)

#MRT PIM
s2.setsockopt(socket.IPPROTO_IP, MRT_PIM, 1)

#ADD VIRTUAL INTERFACE
#estrutura = struct.pack("HBBI 4s 4s", 1, 0x4, 0, 0, socket.inet_aton("192.168.1.112"), socket.inet_aton("224.1.1.112"))
estrutura = struct.pack("HBBI 4s 4s", 0, 0x0, 1, 0, socket.inet_aton("10.0.0.1"), socket.inet_aton("0.0.0.0"))
print(estrutura)
s2.setsockopt(socket.IPPROTO_IP, MRT_ADD_VIF, estrutura)

estrutura = struct.pack("HBBI 4s 4s", 1, 0x0, 1, 0, socket.inet_aton("192.168.2.2"), socket.inet_aton("0.0.0.0"))
print(estrutura)
s2.setsockopt(socket.IPPROTO_IP, MRT_ADD_VIF, estrutura)


#time.sleep(5)

while True:
    print("recv:")
    msg = s2.recv(5000)
    print(len(msg))
    (_, _, im_msgtype, im_mbz, im_vif, _, im_src, im_dst, _) = struct.unpack("II B B B B 4s 4s    8s", msg)
    print(im_msgtype)
    print(im_mbz)
    print(im_vif)
    print(socket.inet_ntoa(im_src))
    print(socket.inet_ntoa(im_dst))
    if im_msgtype == IGMPMSG_NOCACHE:
        print("^^  IGMP NO CACHE")
    print(struct.unpack("II B B B B 4s 4s 8s", msg))



#s2.setsockopt(socket.IPPROTO_IP, MRT_PIM, 1)
#print(s2.getsockopt(socket.IPPROTO_IP, 208))
#s2.setsockopt(socket.IPPROTO_IP, 208, 0)


#ADD MULTICAST FORWARDING ENTRY
estrutura = struct.pack("4s 4s H BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB IIIi", socket.inet_aton("10.0.0.2"), socket.inet_aton("224.1.1.113"), 0, 0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0, 0, 0, 0)
s2.setsockopt(socket.IPPROTO_IP, MRT_ADD_MFC, estrutura)

time.sleep(30)

#MRT DONE
s2.setsockopt(socket.IPPROTO_IP, MRT_DONE, 1)
s2.close()
exit(1)
