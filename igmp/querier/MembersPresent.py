from Packet.PacketIGMPHeader import PacketIGMPHeader
from ..wrapper import Version1MembersPresent, CheckingMembership, NoMembersPresent
from utils import Membership_Query, LastMemberQueryInterval, TYPE_CHECKING
if TYPE_CHECKING:
    from ..GroupState import GroupState


def group_membership_timeout(group_state: 'GroupState'):
    # TODO NOTIFY ROUTING - !!!!
    group_state.state = NoMembersPresent


def group_membership_v1_timeout(group_state: 'GroupState'):
    # do nothing
    return


def retransmit_timeout(group_state: 'GroupState'):
    # do nothing
    return


def receive_v1_membership_report(group_state: 'GroupState'):
    group_state.set_timer()
    group_state.set_v1_host_timer()
    group_state.state = Version1MembersPresent


def receive_v2_membership_report(group_state: 'GroupState'):
    group_state.set_timer()


def receive_leave_group(group_state: 'GroupState'):
    group_ip = group_state.group_ip

    group_state.set_timer(alternative=True)
    group_state.set_retransmit_timer()

    packet = PacketIGMPHeader(type=Membership_Query, max_resp_time=LastMemberQueryInterval*10, group_address=group_ip)
    group_state.router_state.send(data=packet.bytes(), address=group_ip)

    group_state.state = CheckingMembership


def receive_group_specific_query(group_state: 'GroupState', max_response_time):
    # do nothing
    return
