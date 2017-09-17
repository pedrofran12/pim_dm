from ..wrapper import MembersPresent
from ..wrapper import Version1MembersPresent
from utils import TYPE_CHECKING
if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    # do nothing
    return


def group_membership_v1_timeout(group_state: 'GroupState'):
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    # do nothing
    return


def receive_v1_membership_report(group_state: 'GroupState'):
    group_ip = group_state.group_ip
    # TODO NOTIFY ROUTING + !!!!

    group_state.set_timer()
    group_state.set_v1_host_timer()
    group_state.state = Version1MembersPresent


def receive_v2_membership_report(group_state: 'GroupState'):
    group_ip = group_state.group_ip
    # TODO NOTIFY ROUTING + !!!!

    group_state.set_timer()
    group_state.state = MembersPresent


def receive_leave_group(group_state: 'GroupState'):
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    # do nothing
    return