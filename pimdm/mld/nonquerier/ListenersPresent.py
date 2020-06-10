from pimdm.utils import TYPE_CHECKING
from ..wrapper import NoListenersPresent
from ..wrapper import CheckingListeners

if TYPE_CHECKING:
    from ..GroupState import GroupState


def receive_report(group_state: 'GroupState'):
    """
    Received MLD Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('NonQuerier ListenersPresent: receive_report')
    group_state.set_timer()


def receive_done(group_state: 'GroupState'):
    """
    Received MLD Done packet regarding group GroupState
    """
    group_state.group_state_logger.debug('NonQuerier ListenersPresent: receive_done')
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    """
    Received MLD Group Specific Query packet regarding group GroupState
    """
    group_state.group_state_logger.debug('NonQuerier ListenersPresent: receive_group_specific_query')
    group_state.set_timer(alternative=True, max_response_time=max_response_time)
    group_state.set_state(CheckingListeners)


def group_membership_timeout(group_state: 'GroupState'):
    """
    timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('NonQuerier ListenersPresent: group_membership_timeout')
    group_state.set_state(NoListenersPresent)

    # NOTIFY ROUTING - !!!!
    group_state.notify_routing_remove()


def retransmit_timeout(group_state: 'GroupState'):
    """
    retransmit timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('NonQuerier ListenersPresent: retransmit_timeout')
    # do nothing
    return
