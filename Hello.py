from Packet.ReceivedPacket import ReceivedPacket
import Main
from Neighbor import Neighbor


class Hello:
    TYPE = 0
    TRIGGERED_HELLO_DELAY = 16  # TODO: configure via external file??

    def __init__(self):
        Main.add_protocol(Hello.TYPE, self)

    # receive handler
    def receive_handle(self, packet: ReceivedPacket):
        interface = packet.interface
        ip = packet.ip_header.ip_src
        print("ip = ", ip)
        options = packet.payload.payload.get_options()

        if (1 in options) and (20 in options):
            hello_hold_time = options[1]
            generation_id = options[20]
        else:
            raise Exception


        with interface.neighbors_lock.genWlock():
            if ip in interface.neighbors:
                neighbor = interface.neighbors[ip]
            else:
                interface.neighbors[ip] = Neighbor(interface, ip, generation_id, hello_hold_time)
                return

        neighbor.receive_hello(generation_id, hello_hold_time)
"""
with neighbor.neighbor_lock:
    # Already know Neighbor
    print("neighbor conhecido")
    neighbor.heartbeat()
    if neighbor.hello_hold_time != hello_hold_time:
        print("keep alive period diferente")
        neighbor.set_hello_hold_time(hello_hold_time)
    if neighbor.generation_id != generation_id:
        print("neighbor reiniciado")
        neighbor.set_generation_id(generation_id)

with interface.neighbors_lock.genWlock():
    #if interface.get_neighbor(ip) is None:
    if ip in interface.neighbors:
        # Unknown Neighbor
        if (1 in options) and (20 in options):
            try:
                #Main.add_neighbor(packet.interface, ip, options[20], options[1])

                print("non neighbor and options inside")
            except Exception:
                # Received Neighbor with Timeout
                print("non neighbor and options inside but neighbor timedout")
                pass
            return
        print("non neighbor and required options not inside")
    else:
        # Already know Neighbor
        print("neighbor conhecido")
        neighbor = Main.get_neighbor(ip)
        neighbor.heartbeat()
        if 1 in options and neighbor.hello_hold_time != options[1]:
            print("keep alive period diferente")
            neighbor.set_hello_hold_time(options[1])
        if 20 in options and neighbor.generation_id != options[20]:
            print("neighbor reiniciado")
            neighbor.remove()
            Main.add_neighbor(packet.interface, ip, options[20], options[1])
"""