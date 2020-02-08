import logging
from threading import Lock
from threading import Timer

from pimdm.utils import TYPE_CHECKING
from .wrapper import NoMembersPresent
from .igmp_globals import GroupMembershipInterval, LastMemberQueryInterval

if TYPE_CHECKING:
    from .RouterState import RouterState


class GroupState(object):
    LOGGER = logging.getLogger('pim.igmp.RouterState.GroupState')

    def __init__(self, router_state: 'RouterState', group_ip: str):
        #logger
        extra_dict_logger = router_state.router_state_logger.extra.copy()
        extra_dict_logger['tree'] = '(*,' + group_ip + ')'
        self.group_state_logger = logging.LoggerAdapter(GroupState.LOGGER, extra_dict_logger)

        #timers and state
        self.router_state = router_state
        self.group_ip = group_ip
        self.state = NoMembersPresent
        self.timer = None
        self.v1_host_timer = None
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
        self.state = state
        self.group_state_logger.debug("change membership state to: " + state.print_state())

    ###########################################
    # Set timers
    ###########################################
    def set_timer(self, alternative: bool=False, max_response_time: int=None):
        self.clear_timer()
        if not alternative:
            time = GroupMembershipInterval
        else:
            time = self.router_state.interface_state.get_group_membership_time(max_response_time)

        timer = Timer(time, self.group_membership_timeout)
        timer.start()
        self.timer = timer

    def clear_timer(self):
        if self.timer is not None:
            self.timer.cancel()

    def set_v1_host_timer(self):
        self.clear_v1_host_timer()
        v1_host_timer = Timer(GroupMembershipInterval, self.group_membership_v1_timeout)
        v1_host_timer.start()
        self.v1_host_timer = v1_host_timer

    def clear_v1_host_timer(self):
        if self.v1_host_timer is not None:
            self.v1_host_timer.cancel()

    def set_retransmit_timer(self):
        self.clear_retransmit_timer()
        retransmit_timer = Timer(LastMemberQueryInterval, self.retransmit_timeout)
        retransmit_timer.start()
        self.retransmit_timer = retransmit_timer

    def clear_retransmit_timer(self):
        if self.retransmit_timer is not None:
            self.retransmit_timer.cancel()


    ###########################################
    # Get group state from specific interface state
    ###########################################
    def get_interface_group_state(self):
        return self.state.get_state(self.router_state)

    ###########################################
    # Timer timeout
    ###########################################
    def group_membership_timeout(self):
        with self.lock:
            self.get_interface_group_state().group_membership_timeout(self)

    def group_membership_v1_timeout(self):
        with self.lock:
            self.get_interface_group_state().group_membership_v1_timeout(self)

    def retransmit_timeout(self):
        with self.lock:
            self.get_interface_group_state().retransmit_timeout(self)

    ###########################################
    # Receive Packets
    ###########################################
    def receive_v1_membership_report(self):
        with self.lock:
            self.get_interface_group_state().receive_v1_membership_report(self)

    def receive_v2_membership_report(self):
        with self.lock:
            self.get_interface_group_state().receive_v2_membership_report(self)

    def receive_leave_group(self):
        with self.lock:
            self.get_interface_group_state().receive_leave_group(self)

    def receive_group_specific_query(self, max_response_time: int):
        with self.lock:
            self.get_interface_group_state().receive_group_specific_query(self, max_response_time)

    ###########################################
    # Notify Routing
    ###########################################
    def notify_routing_add(self):
        with self.multicast_interface_state_lock:
            print("notify+", self.multicast_interface_state)
            for interface_state in self.multicast_interface_state:
                interface_state.notify_igmp(has_members=True)

    def notify_routing_remove(self):
        with self.multicast_interface_state_lock:
            print("notify-", self.multicast_interface_state)
            for interface_state in self.multicast_interface_state:
                interface_state.notify_igmp(has_members=False)

    def add_multicast_routing_entry(self, kernel_entry):
        with self.multicast_interface_state_lock:
            self.multicast_interface_state.append(kernel_entry)
            return self.has_members()

    def remove_multicast_routing_entry(self, kernel_entry):
        with self.multicast_interface_state_lock:
            self.multicast_interface_state.remove(kernel_entry)

    def has_members(self):
        return self.state is not NoMembersPresent

    def remove(self):
        with self.multicast_interface_state_lock:
            self.clear_retransmit_timer()
            self.clear_timer()
            self.clear_v1_host_timer()
            for interface_state in self.multicast_interface_state:
                interface_state.notify_igmp(has_members=False)
            del self.multicast_interface_state[:]
