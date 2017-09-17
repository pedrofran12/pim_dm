from threading import Timer
import time
from utils import HELLO_HOLD_TIME_NO_TIMEOUT, HELLO_HOLD_TIME_TIMEOUT
from Interface import Interface
import Main


class Neighbor:
    def __init__(self, contact_interface: Interface, ip, generation_id: int, hello_hold_time: int):
        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            raise Exception
        self.contact_interface = contact_interface
        self.ip = ip
        self.generation_id = generation_id
        self.neighbor_liveness_timer = None
        self.hello_hold_time = None
        self.set_hello_hold_time(hello_hold_time)
        self.time_of_last_update = time.time()

    def set_hello_hold_time(self, hello_hold_time: int):
        self.hello_hold_time = hello_hold_time
        if self.neighbor_liveness_timer is not None:
            self.neighbor_liveness_timer.cancel()

        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            self.remove()
        elif hello_hold_time != HELLO_HOLD_TIME_NO_TIMEOUT:
            self.neighbor_liveness_timer = Timer(hello_hold_time, self.remove)
            self.neighbor_liveness_timer.start()
        else:
            self.neighbor_liveness_timer = None

    def heartbeat(self):
        if (self.hello_hold_time != HELLO_HOLD_TIME_TIMEOUT) and \
                (self.hello_hold_time != HELLO_HOLD_TIME_NO_TIMEOUT):
            print("HEARTBEAT")
            if self.neighbor_liveness_timer is not None:
                self.neighbor_liveness_timer.cancel()
            self.neighbor_liveness_timer = Timer(self.hello_hold_time, self.remove)
            self.neighbor_liveness_timer.start()
            self.time_of_last_update = time.time()

    def remove(self):
        print('HELLO TIMER EXPIRED... remove neighbor')
        if self.neighbor_liveness_timer is not None:
            self.neighbor_liveness_timer.cancel()
        Main.remove_neighbor(self.ip)
