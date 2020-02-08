from pimdm.utils import TYPE_CHECKING
if TYPE_CHECKING:
    from ..RouterState import RouterState

def get_state(router_state: 'RouterState'):
    return router_state.interface_state.get_no_members_present_state()


def print_state():
    return "NoMembersPresent"
'''
def group_membership_timeout(group_state):
    get_state(group_state).group_membership_timeout(group_state)


def group_membership_v1_timeout(group_state):
    get_state(group_state).group_membership_v1_timeout(group_state)


def retransmit_timeout(group_state):
    get_state(group_state).retransmit_timeout(group_state)


def receive_v1_membership_report(group_state, packet: ReceivedPacket):
    get_state(group_state).receive_v1_membership_report(group_state, packet)


def receive_v2_membership_report(group_state, packet: ReceivedPacket):
    get_state(group_state).receive_v2_membership_report(group_state, packet)


def receive_leave_group(group_state, packet: ReceivedPacket):
    get_state(group_state).receive_leave_group(group_state, packet)


def receive_group_specific_query(group_state, packet: ReceivedPacket):
    get_state(group_state).receive_group_specific_query(group_state, packet)
'''
