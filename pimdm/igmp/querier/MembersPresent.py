from pimdm.Packet.PacketIGMPHeader import PacketIGMPHeader
from pimdm.utils import TYPE_CHECKING
from ..igmp_globals import Membership_Query, LastMemberQueryInterval
from ..wrapper import Version1MembersPresent, CheckingMembership, NoMembersPresent
if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier MembersPresent: group_membership_timeout')
    group_state.set_state(NoMembersPresent)

    # NOTIFY ROUTING - !!!!
    group_state.notify_routing_remove()


def group_membership_v1_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier MembersPresent: group_membership_v1_timeout')
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier MembersPresent: retransmit_timeout')
    # do nothing
    return


def receive_v1_membership_report(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier MembersPresent: receive_v1_membership_report')
    group_state.set_timer()
    group_state.set_v1_host_timer()
    group_state.set_state(Version1MembersPresent)


def receive_v2_membership_report(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier MembersPresent: receive_v2_membership_report')
    group_state.set_timer()


def receive_leave_group(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier MembersPresent: receive_leave_group')
    group_ip = group_state.group_ip

    group_state.set_timer(alternative=True)
    group_state.set_retransmit_timer()

    packet = PacketIGMPHeader(type=Membership_Query, max_resp_time=LastMemberQueryInterval*10, group_address=group_ip)
    group_state.router_state.send(data=packet.bytes(), address=group_ip)

    group_state.set_state(CheckingMembership)


def receive_group_specific_query(group_state: 'GroupState', max_response_time):
    group_state.group_state_logger.debug('Querier MembersPresent: receive_group_specific_query')
    # do nothing
    return
