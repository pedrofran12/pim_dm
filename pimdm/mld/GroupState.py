import logging
from threading import Lock
from threading import Timer

from pimdm.utils import TYPE_CHECKING
from .wrapper import NoListenersPresent
from .mld_globals import MULTICAST_LISTENER_INTERVAL, LAST_LISTENER_QUERY_INTERVAL

if TYPE_CHECKING:
    from .RouterState import RouterState


class GroupState(object):
    LOGGER = logging.getLogger('pim.mld.RouterState.GroupState')

    def __init__(self, router_state: 'RouterState', group_ip: str):
        #logger
        extra_dict_logger = router_state.router_state_logger.extra.copy()
        extra_dict_logger['tree'] = '(*,' + group_ip + ')'
        self.group_state_logger = logging.LoggerAdapter(GroupState.LOGGER, extra_dict_logger)

        #timers and state
        self.router_state = router_state
        self.group_ip = group_ip
        self.state = NoListenersPresent
        self.timer = None
        self.retransmit_timer = None
        # lock
        self.lock = Lock()

        # KernelEntry's instances to notify change of igmp state
        self.multicast_interface_state = []
        self.multicast_interface_state_lock = Lock()

    def print_state(self):
        return self.state.print_state()

    ###########################################
    # Set state
    ###########################################
    def set_state(self, state):
        """
        Set membership state regarding this Group
        """
        self.state = state
        self.group_state_logger.debug("change membership state to: " + state.print_state())

    ###########################################
    # Set timers
    ###########################################
    def set_timer(self, alternative: bool = False, max_response_time: int = None):
        """
        Set timer
        """
        self.clear_timer()
        if not alternative:
            time = MULTICAST_LISTENER_INTERVAL
        else:
            time = self.router_state.interface_state.get_group_membership_time(max_response_time)

        timer = Timer(time, self.group_membership_timeout)
        timer.start()
        self.timer = timer

    def clear_timer(self):
        """
        Stop timer
        """
        if self.timer is not None:
            self.timer.cancel()

    def set_retransmit_timer(self):
        """
        Set retransmit timer
        """
        self.clear_retransmit_timer()
        retransmit_timer = Timer(LAST_LISTENER_QUERY_INTERVAL, self.retransmit_timeout)
        retransmit_timer.start()
        self.retransmit_timer = retransmit_timer

    def clear_retransmit_timer(self):
        """
        Stop retransmit timer
        """
        if self.retransmit_timer is not None:
            self.retransmit_timer.cancel()

    ###########################################
    # Get group state from specific interface state
    ###########################################
    def get_interface_group_state(self):
        """
        Get specific implementation of the membership state machine (depending on the querier state machine)
        """
        return self.state.get_state(self.router_state)

    ###########################################
    # Timer timeout
    ###########################################
    def group_membership_timeout(self):
        """
        Timer has expired
        """
        with self.lock:
            self.get_interface_group_state().group_membership_timeout(self)

    def retransmit_timeout(self):
        """
        Retransmit timer has expired
        """
        with self.lock:
            self.get_interface_group_state().retransmit_timeout(self)

    ###########################################
    # Receive Packets
    ###########################################
    def receive_report(self):
        """
        Received MLD Report packet regarding this group
        """
        with self.lock:
            self.get_interface_group_state().receive_report(self)

    def receive_done(self):
        """
        Received MLD Done packet regarding this group
        """
        with self.lock:
            self.get_interface_group_state().receive_done(self)

    def receive_group_specific_query(self, max_response_time: int):
        """
        Received MLD Group Specific Query packet regarding this group
        """
        with self.lock:
            self.get_interface_group_state().receive_group_specific_query(self, max_response_time)

    ###########################################
    # Notify Routing
    ###########################################
    def notify_routing_add(self):
        """
        Notify all tree entries that MLD considers to have hosts interested in this group
        """
        with self.multicast_interface_state_lock:
            print("notify+", self.multicast_interface_state)
            for interface_state in self.multicast_interface_state:
                interface_state.notify_membership(has_members=True)

    def notify_routing_remove(self):
        """
        Notify all tree entries that MLD considers to have not hosts interested in this group
        """
        with self.multicast_interface_state_lock:
            print("notify-", self.multicast_interface_state)
            for interface_state in self.multicast_interface_state:
                interface_state.notify_membership(has_members=False)

    def add_multicast_routing_entry(self, kernel_entry):
        """
        A new tree is being monitored by the multicast routing protocol that has the same group
        MLD will store these entries in order to accelerate the notification process regarding changes in MLD state
        """
        with self.multicast_interface_state_lock:
            self.multicast_interface_state.append(kernel_entry)
            return self.has_members()

    def remove_multicast_routing_entry(self, kernel_entry):
        """
        A tree is no longer being monitored by the multicast routing protocol
        Remove this tree from this object
        """
        with self.multicast_interface_state_lock:
            self.multicast_interface_state.remove(kernel_entry)

    def has_members(self):
        """
        Determine if MLD considers to have hosts interested in receiving data packets
        """
        return self.state is not NoListenersPresent

    def remove(self):
        """
        Remove this group from the MLD process
        Notify all trees that this group no longer considers to be connected to hosts
        This method will be invoked whenever an MLD interface is removed
        """
        with self.multicast_interface_state_lock:
            self.clear_retransmit_timer()
            self.clear_timer()
            for interface_state in self.multicast_interface_state:
                interface_state.notify_membership(has_members=False)
            del self.multicast_interface_state[:]
