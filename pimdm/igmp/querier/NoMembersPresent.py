from pimdm.utils import TYPE_CHECKING
from ..wrapper import MembersPresent
from ..wrapper import Version1MembersPresent
if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    """
    timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: group_membership_timeout')
    # do nothing
    return


def group_membership_v1_timeout(group_state: 'GroupState'):
    """
    v1 host timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: group_membership_v1_timeout')
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    """
    retransmit timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: retransmit_timeout')
    # do nothing
    return


def receive_v1_membership_report(group_state: 'GroupState'):
    """
    Received IGMP Version 1 Membership Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: receive_v1_membership_report')
    group_state.set_timer()
    group_state.set_v1_host_timer()
    group_state.set_state(Version1MembersPresent)

    # NOTIFY ROUTING + !!!!
    group_state.notify_routing_add()


def receive_v2_membership_report(group_state: 'GroupState'):
    """
    Received IGMP Membership Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: receive_v2_membership_report')
    group_state.set_timer()
    group_state.set_state(MembersPresent)

    # NOTIFY ROUTING + !!!!
    group_state.notify_routing_add()


def receive_leave_group(group_state: 'GroupState'):
    """
    Received IGMP Leave packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: receive_leave_group')
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    """
    Received IGMP Group Specific Query packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoMembersPresent: receive_group_specific_query')
    # do nothing
    return
