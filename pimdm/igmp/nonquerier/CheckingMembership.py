from pimdm.utils import TYPE_CHECKING
from ..wrapper import NoMembersPresent
from ..wrapper import MembersPresent

if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: group_membership_timeout')
    group_state.set_state(NoMembersPresent)

    # NOTIFY ROUTING - !!!!
    group_state.notify_routing_remove()


def group_membership_v1_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: group_membership_v1_timeout')
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: retransmit_timeout')
    # do nothing
    return


def receive_v1_membership_report(group_state: 'GroupState'):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: receive_v1_membership_report')
    receive_v2_membership_report(group_state)


def receive_v2_membership_report(group_state: 'GroupState'):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: receive_v2_membership_report')
    group_state.set_timer()
    group_state.set_state(MembersPresent)


def receive_leave_group(group_state: 'GroupState'):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: receive_leave_group')
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    group_state.group_state_logger.debug('NonQuerier CheckingMembership: receive_group_specific_query')
    # do nothing
    return
