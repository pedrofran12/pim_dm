from pimdm.utils import TYPE_CHECKING
from pimdm.packet.PacketIGMPHeader import PacketIGMPHeader
from pimdm.igmp.igmp_globals import MEMBERSHIP_QUERY, LAST_MEMBER_QUERY_INTERVAL
from ..wrapper import Version1MembersPresent, CheckingMembership, NoMembersPresent
if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    """
    timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier MembersPresent: group_membership_timeout')
    group_state.set_state(NoMembersPresent)

    # NOTIFY ROUTING - !!!!
    group_state.notify_routing_remove()


def group_membership_v1_timeout(group_state: 'GroupState'):
    """
    v1 host timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier MembersPresent: group_membership_v1_timeout')
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    """
    retransmit timer associated with group GroupState object has expired
    """
    group_state.group_state_logger.debug('Querier MembersPresent: retransmit_timeout')
    # do nothing
    return


def receive_v1_membership_report(group_state: 'GroupState'):
    """
    Received IGMP Version 1 Membership Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier MembersPresent: receive_v1_membership_report')
    group_state.set_timer()
    group_state.set_v1_host_timer()
    group_state.set_state(Version1MembersPresent)


def receive_v2_membership_report(group_state: 'GroupState'):
    """
    Received IGMP Membership Report packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier MembersPresent: receive_v2_membership_report')
    group_state.set_timer()


def receive_leave_group(group_state: 'GroupState'):
    """
    Received IGMP Leave packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier MembersPresent: receive_leave_group')
    group_ip = group_state.group_ip

    group_state.set_timer(alternative=True)
    group_state.set_retransmit_timer()

    packet = PacketIGMPHeader(type=MEMBERSHIP_QUERY, max_resp_time=LAST_MEMBER_QUERY_INTERVAL * 10,
                              group_address=group_ip)
    group_state.router_state.send(data=packet.bytes(), address=group_ip)

    group_state.set_state(CheckingMembership)


def receive_group_specific_query(group_state: 'GroupState', max_response_time):
    """
    Received IGMP Group Specific Query packet regarding group GroupState
    """
    group_state.group_state_logger.debug('Querier MembersPresent: receive_group_specific_query')
    # do nothing
    return
