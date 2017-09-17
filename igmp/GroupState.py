from threading import Timer
from .wrapper import NoMembersPresent
from utils import GroupMembershipInterval, LastMemberQueryInterval, TYPE_CHECKING
from threading import Lock

if TYPE_CHECKING:
    from .RouterState import RouterState


class GroupState(object):
    def __init__(self, router_state: 'RouterState', group_ip: str):
        self.router_state = router_state
        self.group_ip = group_ip
        self.state = NoMembersPresent
        self.timer = None
        self.v1_host_timer = None
        self.retransmit_timer = None
        # lock
        self.lock = Lock()

    def print_state(self):
        return self.state.print_state()

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
