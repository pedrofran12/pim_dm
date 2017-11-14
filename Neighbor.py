from threading import Timer
import time
from utils import HELLO_HOLD_TIME_NO_TIMEOUT, HELLO_HOLD_TIME_TIMEOUT, TYPE_CHECKING
from threading import Lock
from RWLock.RWLock import RWLockWrite
import Main
if TYPE_CHECKING:
    from InterfacePIM import InterfacePim


class Neighbor:
    def __init__(self, contact_interface: "InterfacePim", ip, generation_id: int, hello_hold_time: int):
        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            raise Exception
        self.contact_interface = contact_interface
        self.ip = ip
        self.generation_id = generation_id
        # todo lan prune delay
        # todo override interval
        # todo state refresh capable

        self.neighbor_liveness_timer = None
        self.hello_hold_time = None
        self.set_hello_hold_time(hello_hold_time)
        self.time_of_last_update = time.time()
        self.neighbor_lock = Lock()

        self.tree_interface_nlt_subscribers = []
        self.tree_interface_nlt_subscribers_lock = RWLockWrite()


        # send hello to new neighbor
        #self.contact_interface.send_hello()
        # todo RANDOM DELAY??? => DO NOTHING... EVENTUALLY THE HELLO MESSAGE WILL BE SENT

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

    def set_generation_id(self, generation_id):
        # neighbor restarted
        if self.generation_id != generation_id:
            self.generation_id = generation_id
            self.contact_interface.send_hello()
            self.reset()

    """
    def heartbeat(self):
        if (self.hello_hold_time != HELLO_HOLD_TIME_TIMEOUT) and \
                (self.hello_hold_time != HELLO_HOLD_TIME_NO_TIMEOUT):
            print("HEARTBEAT")
            if self.neighbor_liveness_timer is not None:
                self.neighbor_liveness_timer.cancel()
            self.neighbor_liveness_timer = Timer(self.hello_hold_time, self.remove)
            self.neighbor_liveness_timer.start()
            self.time_of_last_update = time.time()
    """

    def remove(self):
        print('HELLO TIMER EXPIRED... remove neighbor')
        if self.neighbor_liveness_timer is not None:
            self.neighbor_liveness_timer.cancel()
        #Main.remove_neighbor(self.ip)
        interface_name = self.contact_interface.interface_name
        neighbor_ip = self.ip

        del self.contact_interface.neighbors[self.ip]

        # notify interfaces which have this neighbor as AssertWinner
        with self.tree_interface_nlt_subscribers_lock.genRlock():
            for tree_if in self.tree_interface_nlt_subscribers:
                tree_if.assert_winner_nlt_expires()


    def reset(self):
        return


    def receive_hello(self, generation_id, hello_hold_time):
        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            self.set_hello_hold_time(hello_hold_time)
        else:
            self.time_of_last_update = time.time()
            self.set_generation_id(generation_id)
            self.set_hello_hold_time(hello_hold_time)



    def subscribe_nlt_expiration(self, tree_if):
        with self.tree_interface_nlt_subscribers_lock.genWlock():
            if tree_if not in self.tree_interface_nlt_subscribers:
                self.tree_interface_nlt_subscribers.append(tree_if)

    def unsubscribe_nlt_expiration(self, tree_if):
        with self.tree_interface_nlt_subscribers_lock.genWlock():
            if tree_if in self.tree_interface_nlt_subscribers:
                self.tree_interface_nlt_subscribers.remove(tree_if)
