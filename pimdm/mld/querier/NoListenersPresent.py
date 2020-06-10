from pimdm.utils import TYPE_CHECKING
from ..wrapper import ListenersPresent
if TYPE_CHECKING:
    from ..GroupState import GroupState


def receive_report(group_state: 'GroupState'):
    """
    Received MLD Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoListenersPresent: receive_report')
    group_state.set_timer()
    group_state.set_state(ListenersPresent)

    # NOTIFY ROUTING + !!!!
    group_state.notify_routing_add()


def receive_done(group_state: 'GroupState'):
    """
    Received MLD Done packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoListenersPresent: receive_done')
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    """
    Received MLD Group Specific Query packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier NoListenersPresent: receive_group_specific_query')
    # do nothing
    return


def group_membership_timeout(group_state: 'GroupState'):
    """
    timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier NoListenersPresent: group_membership_timeout')
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    """
    retransmit timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier NoListenersPresent: retransmit_timeout')
    # do nothing
    return
