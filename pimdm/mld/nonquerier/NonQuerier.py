from ipaddress import IPv6Address
from pimdm.utils import TYPE_CHECKING
from ..mld_globals import QueryResponseInterval, LastListenerQueryCount
from pimdm.packet.PacketMLDHeader import PacketMLDHeader
from pimdm.packet.ReceivedPacket import ReceivedPacket
from . import NoListenersPresent, ListenersPresent, CheckingListeners

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
        packet = PacketMLDHeader(type=PacketMLDHeader.MULTICAST_LISTENER_QUERY_TYPE,
                                 max_resp_delay=QueryResponseInterval*1000)
        router_state.interface.send(packet.bytes())

        # set general query timer
        router_state.set_general_query_timer()

    @staticmethod
    def receive_query(router_state: 'RouterState', packet: ReceivedPacket):
        router_state.router_state_logger.debug('NonQuerier state: receive_query')
        source_ip = packet.ip_header.ip_src

        # if source ip of membership query not lower than the ip of the received interface => ignore
        if IPv6Address(source_ip) >= IPv6Address(router_state.interface.get_ip()):
            return

        # reset other present querier timer
        router_state.set_other_querier_present_timer()

    # TODO ver se existe uma melhor maneira de fazer isto
    @staticmethod
    def state_name():
        return "Non Querier"

    @staticmethod
    def get_group_membership_time(max_response_time: int):
        return (max_response_time/1000.0) * LastListenerQueryCount

    # State
    @staticmethod
    def get_checking_listeners_state():
        return CheckingListeners

    @staticmethod
    def get_listeners_present_state():
        return ListenersPresent

    @staticmethod
    def get_no_listeners_present_state():
        return NoListenersPresent
