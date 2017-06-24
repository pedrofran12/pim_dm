from threading import Timer
from utils import KEEP_ALIVE_PERIOD_NO_TIMEOUT, KEEP_ALIVE_PERIOD_TIMEOUT
from Interface import Interface


class Neighbor:
    def __init__(self, contact_interface: Interface, ip, generation_id: int, keep_alive_period: int):
        self.contact_interface = contact_interface
        self.ip = ip
        self.generation_id = generation_id
        self.neighbor_liveness_timer = None
        self.set_keep_alive_period(keep_alive_period)

    def set_keep_alive_period(self, keep_alive_period: int):
        self.keep_alive_period = keep_alive_period
        if self.neighbor_liveness_timer is not None:
            self.neighbor_liveness_timer.cancel()

        if keep_alive_period == KEEP_ALIVE_PERIOD_TIMEOUT:
            self.remove()
        elif keep_alive_period != KEEP_ALIVE_PERIOD_NO_TIMEOUT:
            self.neighbor_liveness_timer = Timer(4 * keep_alive_period, self.remove)
            self.neighbor_liveness_timer.start()
        else:
            self.neighbor_liveness_timer = None

    def heartbeat(self):
        if (self.keep_alive_period != KEEP_ALIVE_PERIOD_TIMEOUT) and \
                (self.keep_alive_period != KEEP_ALIVE_PERIOD_NO_TIMEOUT):
            print("HEARTBEAT")
            if self.neighbor_liveness_timer is not None:
                self.neighbor_liveness_timer.cancel()
            self.neighbor_liveness_timer = Timer(4 * self.keep_alive_period, self.remove)
            self.neighbor_liveness_timer.start()

    def remove(self):
        from Main import Main
        print('HELLO TIMER EXPIRED... remove neighbor')
        if self.neighbor_liveness_timer is not None:
            self.neighbor_liveness_timer.cancel()
        Main().remove_neighbor(self.ip)
