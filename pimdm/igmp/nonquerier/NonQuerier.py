from ipaddress import IPv4Address
from pimdm.utils import TYPE_CHECKING
from ..igmp_globals import Membership_Query, QueryResponseInterval, LastMemberQueryCount
from pimdm.Packet.PacketIGMPHeader import PacketIGMPHeader
from pimdm.Packet.ReceivedPacket import ReceivedPacket
from . import NoMembersPresent, MembersPresent, CheckingMembership

if TYPE_CHECKING:
    from ..RouterState import RouterState


class NonQuerier:

    @staticmethod
    def general_query_timeout(router_state: 'RouterState'):
        router_state.router_state_logger.debug('NonQuerier state: general_query_timeout')
        # do nothing
        return

    @staticmethod
    def other_querier_present_timeout(router_state: 'RouterState'):
        router_state.router_state_logger.debug('NonQuerier state: other_querier_present_timeout')
        #change state to Querier
        router_state.change_interface_state(querier=True)

        # send general query
        packet = PacketIGMPHeader(type=Membership_Query, max_resp_time=QueryResponseInterval*10)
        router_state.interface.send(packet.bytes())

        # set general query timer
        router_state.set_general_query_timer()

    @staticmethod
    def receive_query(router_state: 'RouterState', packet: ReceivedPacket):
        router_state.router_state_logger.debug('NonQuerier state: receive_query')
        source_ip = packet.ip_header.ip_src

        # if source ip of membership query not lower than the ip of the received interface => ignore
        if IPv4Address(source_ip) >= IPv4Address(router_state.interface.get_ip()):
            return

        # reset other present querier timer
        router_state.set_other_querier_present_timer()

    # TODO ver se existe uma melhor maneira de fazer isto
    @staticmethod
    def state_name():
        return "Non Querier"

    @staticmethod
    def get_group_membership_time(max_response_time: int):
        return (max_response_time/10.0) * LastMemberQueryCount

    # State
    @staticmethod
    def get_checking_membership_state():
        return CheckingMembership

    @staticmethod
    def get_members_present_state():
        return MembersPresent

    @staticmethod
    def get_no_members_present_state():
        return NoMembersPresent

    @staticmethod
    def get_version_1_members_present_state():
        return NonQuerier.get_members_present_state()
