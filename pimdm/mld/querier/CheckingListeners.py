from pimdm.packet.PacketMLDHeader import PacketMLDHeader
from pimdm.utils import TYPE_CHECKING
from ..mld_globals import LastListenerQueryInterval
from ..wrapper import ListenersPresent, NoListenersPresent
if TYPE_CHECKING:
    from ..GroupState import GroupState


def receive_report(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier CheckingListeners: receive_report')
    group_state.set_timer()
    group_state.clear_retransmit_timer()
    group_state.set_state(ListenersPresent)

def receive_done(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier CheckingListeners: receive_done')
    # do nothing
    return


def receive_group_specific_query(group_state: 'GroupState', max_response_time: int):
    group_state.group_state_logger.debug('Querier CheckingListeners: receive_group_specific_query')
    # do nothing
    return


def group_membership_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier CheckingListeners: group_membership_timeout')
    group_state.clear_retransmit_timer()
    group_state.set_state(NoListenersPresent)

    # NOTIFY ROUTING - !!!!
    group_state.notify_routing_remove()


def retransmit_timeout(group_state: 'GroupState'):
    group_state.group_state_logger.debug('Querier CheckingListeners: retransmit_timeout')
    group_addr = group_state.group_ip
    packet = PacketMLDHeader(type=PacketMLDHeader.MULTICAST_LISTENER_QUERY_TYPE,
                             max_resp_delay=LastListenerQueryInterval*1000, group_address=group_addr)
    group_state.router_state.send(data=packet.bytes(), address=group_addr)

    group_state.set_retransmit_timer()
