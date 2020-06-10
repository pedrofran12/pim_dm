from pimdm.packet.PacketIGMPHeader import PacketIGMPHeader
from pimdm.utils import TYPE_CHECKING
from pimdm.igmp.igmp_globals import MEMBERSHIP_QUERY, LAST_MEMBER_QUERY_INTERVAL
from ..wrapper import NoMembersPresent, MembersPresent, Version1MembersPresent
if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    """
    timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: group_membership_timeout')
    group_state.clear_retransmit_timer()
    group_state.set_state(NoMembersPresent)

    # NOTIFY ROUTING - !!!!
    group_state.notify_routing_remove()


def group_membership_v1_timeout(group_state: 'GroupState'):
    """
    v1 host timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: group_membership_v1_timeout')
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    """
    retransmit timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: retransmit_timeout')
    group_addr = group_state.group_ip
    packet = PacketIGMPHeader(type=MEMBERSHIP_QUERY, max_resp_time=LAST_MEMBER_QUERY_INTERVAL * 10,
                              group_address=group_addr)
    group_state.router_state.send(data=packet.bytes(), address=group_addr)

    group_state.set_retransmit_timer()


def receive_v1_membership_report(group_state: 'GroupState'):
    """
    Received IGMP Version 1 Membership Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: receive_v1_membership_report')
    group_state.set_timer()
    group_state.set_v1_host_timer()
    group_state.set_state(Version1MembersPresent)


def receive_v2_membership_report(group_state: 'GroupState'):
    """
    Received IGMP Membership Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: receive_v2_membership_report')
    group_state.set_timer()
    group_state.set_state(MembersPresent)


def receive_leave_group(group_state: 'GroupState'):
    """
    Received IGMP Leave packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: receive_leave_group')
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    """
    Received IGMP Group Specific Query packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier CheckingMembership: receive_group_specific_query')
    # do nothing
    return
