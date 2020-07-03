import time
import logging
from threading import Timer
from threading import Lock, RLock

from pimdm.tree.pim_globals import HELLO_HOLD_TIME_NO_TIMEOUT, HELLO_HOLD_TIME_TIMEOUT
from pimdm.utils import TYPE_CHECKING
if TYPE_CHECKING:
    from pimdm.InterfacePIM import InterfacePim


class Neighbor:
    LOGGER = logging.getLogger('pim.Interface.Neighbor')

    def __init__(self, contact_interface: "InterfacePim", ip, generation_id: int, hello_hold_time: int,
                 state_refresh_capable: bool):
        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            raise Exception
        logger_info = dict(contact_interface.interface_logger.extra)
        logger_info['neighbor_ip'] = ip
        self.neighbor_logger = logging.LoggerAdapter(self.LOGGER, logger_info)
        self.neighbor_logger.debug('Monitoring new neighbor ' + ip + ' with GenerationID: ' + str(generation_id) +
                                   '; HelloHoldTime: ' + str(hello_hold_time) + '; StateRefreshCapable: ' +
                                   str(state_refresh_capable))
        self.contact_interface = contact_interface
        self.ip = ip
        self.generation_id = generation_id
        # todo lan prune delay
        # todo override interval
        self.state_refresh_capable = state_refresh_capable

        self.neighbor_liveness_timer = None
        self.hello_hold_time = None
        self.set_hello_hold_time(hello_hold_time)
        self.time_of_last_update = time.time()
        self.neighbor_lock = Lock()

        self.tree_interface_nlt_subscribers = []
        self.tree_interface_nlt_subscribers_lock = RLock()

    def set_hello_hold_time(self, hello_hold_time: int):
        self.hello_hold_time = hello_hold_time
        if self.neighbor_liveness_timer is not None:
            self.neighbor_liveness_timer.cancel()

        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            self.remove()
            self.neighbor_logger.debug('Detected neighbor removal of ' + self.ip)
        elif hello_hold_time != HELLO_HOLD_TIME_NO_TIMEOUT:
            self.neighbor_logger.debug('Neighbor Liveness Timer reseted of ' + self.ip)
            self.neighbor_liveness_timer = Timer(hello_hold_time, self.remove)
            self.neighbor_liveness_timer.start()
        else:
            self.neighbor_liveness_timer = None

    def set_generation_id(self, generation_id):
        # neighbor restarted
        if self.generation_id != generation_id:
            self.neighbor_logger.debug('Detected reset of ' + self.ip + '... new GenerationID: ' + str(generation_id))
            self.generation_id = generation_id
            self.contact_interface.force_send_hello()
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
        self.neighbor_logger.debug('Neighbor Liveness Timer expired of ' + self.ip)
        self.contact_interface.remove_neighbor(self.ip)

        # notify interfaces which have this neighbor as AssertWinner
        with self.tree_interface_nlt_subscribers_lock:
            for tree_if in self.tree_interface_nlt_subscribers:
                tree_if.assert_winner_nlt_expires()

    def reset(self):
        self.contact_interface.new_or_reset_neighbor(self.ip)

    def receive_hello(self, generation_id, hello_hold_time, state_refresh_capable):
        self.neighbor_logger.debug('Receive Hello message with HelloHoldTime: ' + str(hello_hold_time) +
                                   '; GenerationID: ' + str(generation_id) + '; StateRefreshCapable: ' +
                                   str(state_refresh_capable) + ' from neighbor ' + self.ip)
        if hello_hold_time == HELLO_HOLD_TIME_TIMEOUT:
            self.set_hello_hold_time(hello_hold_time)
        else:
            self.time_of_last_update = time.time()
            self.set_generation_id(generation_id)
            self.set_hello_hold_time(hello_hold_time)
        if state_refresh_capable != self.state_refresh_capable:
            self.state_refresh_capable = state_refresh_capable

    def subscribe_nlt_expiration(self, tree_if):
        with self.tree_interface_nlt_subscribers_lock:
            if tree_if not in self.tree_interface_nlt_subscribers:
                self.tree_interface_nlt_subscribers.append(tree_if)

    def unsubscribe_nlt_expiration(self, tree_if):
        with self.tree_interface_nlt_subscribers_lock:
            if tree_if in self.tree_interface_nlt_subscribers:
                self.tree_interface_nlt_subscribers.remove(tree_if)
