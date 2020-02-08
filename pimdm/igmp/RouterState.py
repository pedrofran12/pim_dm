from threading import Timer
import logging

from pimdm.Packet.PacketIGMPHeader import PacketIGMPHeader
from pimdm.Packet.ReceivedPacket import ReceivedPacket
from pimdm.utils import TYPE_CHECKING
from pimdm.RWLock.RWLock import RWLockWrite
from .querier.Querier import Querier
from .nonquerier.NonQuerier import NonQuerier
from .GroupState import GroupState
from .igmp_globals import Membership_Query, QueryResponseInterval, QueryInterval, OtherQuerierPresentInterval

if TYPE_CHECKING:
    from pimdm.InterfaceIGMP import InterfaceIGMP


class RouterState(object):
    ROUTER_STATE_LOGGER = logging.getLogger('pim.igmp.RouterState')

    def __init__(self, interface: 'InterfaceIGMP'):
        #logger
        logger_extra = dict()
        logger_extra['vif'] = interface.vif_index
        logger_extra['interfacename'] = interface.interface_name
        self.router_state_logger = logging.LoggerAdapter(RouterState.ROUTER_STATE_LOGGER, logger_extra)

        # interface of the router connected to the network
        self.interface = interface

        # state of the router (Querier/NonQuerier)
        self.interface_state = Querier

        # state of each group
        # Key: GroupIPAddress, Value: GroupState object
        self.group_state = {}
        self.group_state_lock = RWLockWrite()

        # send general query
        packet = PacketIGMPHeader(type=Membership_Query, max_resp_time=QueryResponseInterval*10)
        self.interface.send(packet.bytes())

        # set initial general query timer
        timer = Timer(QueryInterval, self.general_query_timeout)
        timer.start()
        self.general_query_timer = timer

        # present timer
        self.other_querier_present_timer = None

    # Send packet via interface
    def send(self, data: bytes, address: str):
        self.interface.send(data, address)

    ############################################
    # interface_state methods
    ############################################
    def print_state(self):
        return self.interface_state.state_name()

    def set_general_query_timer(self):
        self.clear_general_query_timer()
        general_query_timer = Timer(QueryInterval, self.general_query_timeout)
        general_query_timer.start()
        self.general_query_timer = general_query_timer

    def clear_general_query_timer(self):
        if self.general_query_timer is not None:
            self.general_query_timer.cancel()

    def set_other_querier_present_timer(self):
        self.clear_other_querier_present_timer()
        other_querier_present_timer = Timer(OtherQuerierPresentInterval, self.other_querier_present_timeout)
        other_querier_present_timer.start()
        self.other_querier_present_timer = other_querier_present_timer

    def clear_other_querier_present_timer(self):
        if self.other_querier_present_timer is not None:
            self.other_querier_present_timer.cancel()

    def general_query_timeout(self):
        self.interface_state.general_query_timeout(self)

    def other_querier_present_timeout(self):
        self.interface_state.other_querier_present_timeout(self)

    def change_interface_state(self, querier: bool):
        if querier:
            self.interface_state = Querier
            self.router_state_logger.debug('change querier state to -> Querier')
        else:
            self.interface_state = NonQuerier
            self.router_state_logger.debug('change querier state to -> NonQuerier')

    ############################################
    # group state methods
    ############################################
    def get_group_state(self, group_ip):
        with self.group_state_lock.genRlock():
            if group_ip in self.group_state:
                return self.group_state[group_ip]

        with self.group_state_lock.genWlock():
            if group_ip in self.group_state:
                group_state = self.group_state[group_ip]
            else:
                group_state = GroupState(self, group_ip)
                self.group_state[group_ip] = group_state
            return group_state

    def receive_v1_membership_report(self, packet: ReceivedPacket):
        igmp_group = packet.payload.group_address
        #if igmp_group not in self.group_state:
        #    self.group_state[igmp_group] = GroupState(self, igmp_group)

        #self.group_state[igmp_group].receive_v1_membership_report()
        self.get_group_state(igmp_group).receive_v1_membership_report()

    def receive_v2_membership_report(self, packet: ReceivedPacket):
        igmp_group = packet.payload.group_address
        #if igmp_group not in self.group_state:
        #    self.group_state[igmp_group] = GroupState(self, igmp_group)

        #self.group_state[igmp_group].receive_v2_membership_report()
        self.get_group_state(igmp_group).receive_v2_membership_report()

    def receive_leave_group(self, packet: ReceivedPacket):
        igmp_group = packet.payload.group_address
        #if igmp_group in self.group_state:
        #    self.group_state[igmp_group].receive_leave_group()
        self.get_group_state(igmp_group).receive_leave_group()

    def receive_query(self, packet: ReceivedPacket):
        self.interface_state.receive_query(self, packet)
        igmp_group = packet.payload.group_address

        # process group specific query
        if igmp_group != "0.0.0.0" and igmp_group in self.group_state:
        #if igmp_group != "0.0.0.0":
            max_response_time = packet.payload.max_resp_time
            #self.group_state[igmp_group].receive_group_specific_query(max_response_time)
            self.get_group_state(igmp_group).receive_group_specific_query(max_response_time)

    def remove(self):
        for group in self.group_state.values():
            group.remove()