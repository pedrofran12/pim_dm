import logging
from threading import Timer

from pimdm.packet.PacketMLDHeader import PacketMLDHeader
from pimdm.packet.ReceivedPacket import ReceivedPacket
from pimdm.utils import TYPE_CHECKING
from pimdm.rwlock.RWLock import RWLockWrite
from .querier.Querier import Querier
from .nonquerier.NonQuerier import NonQuerier
from .GroupState import GroupState
from .mld_globals import QUERY_RESPONSE_INTERVAL, QUERY_INTERVAL, OTHER_QUERIER_PRESENT_INTERVAL, \
    MULTICAST_LISTENER_QUERY_TYPE

if TYPE_CHECKING:
    from pimdm.InterfaceMLD import InterfaceMLD


class RouterState(object):
    ROUTER_STATE_LOGGER = logging.getLogger('pim.mld.RouterState')

    def __init__(self, interface: 'InterfaceMLD'):
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
        packet = PacketMLDHeader(type=MULTICAST_LISTENER_QUERY_TYPE, max_resp_delay=QUERY_RESPONSE_INTERVAL * 1000)
        self.interface.send(packet.bytes())

        # set initial general query timer
        timer = Timer(QUERY_INTERVAL, self.general_query_timeout)
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
        """
        Set general query timer
        """
        self.clear_general_query_timer()
        general_query_timer = Timer(QUERY_INTERVAL, self.general_query_timeout)
        general_query_timer.start()
        self.general_query_timer = general_query_timer

    def clear_general_query_timer(self):
        """
        Stop general query timer
        """
        if self.general_query_timer is not None:
            self.general_query_timer.cancel()

    def set_other_querier_present_timer(self):
        """
        Set other querier present timer
        """
        self.clear_other_querier_present_timer()
        other_querier_present_timer = Timer(OTHER_QUERIER_PRESENT_INTERVAL, self.other_querier_present_timeout)
        other_querier_present_timer.start()
        self.other_querier_present_timer = other_querier_present_timer

    def clear_other_querier_present_timer(self):
        """
        Stop other querier present timer
        """
        if self.other_querier_present_timer is not None:
            self.other_querier_present_timer.cancel()

    def general_query_timeout(self):
        """
        General Query timer has expired
        """
        self.interface_state.general_query_timeout(self)

    def other_querier_present_timeout(self):
        """
        Other Querier Present timer has expired
        """
        self.interface_state.other_querier_present_timeout(self)

    def change_interface_state(self, querier: bool):
        """
        Change state regarding querier state machine (Querier/NonQuerier)
        """
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
        """
        Get object that monitors a given group (with group_ip IP address)
        """
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

    def receive_report(self, packet: ReceivedPacket):
        """
        Received MLD Report packet
        """
        mld_group = packet.payload.group_address
        self.get_group_state(mld_group).receive_report()

    def receive_done(self, packet: ReceivedPacket):
        """
        Received MLD Done packet
        """
        mld_group = packet.payload.group_address
        self.get_group_state(mld_group).receive_done()

    def receive_query(self, packet: ReceivedPacket):
        """
        Received MLD Query packet
        """
        self.interface_state.receive_query(self, packet)
        mld_group = packet.payload.group_address

        # process group specific query
        if mld_group != "::" and mld_group in self.group_state:
            max_response_time = packet.payload.max_resp_delay
            self.get_group_state(mld_group).receive_group_specific_query(max_response_time)

    def remove(self):
        """
        Remove this MLD interface
        Clear all state
        """
        for group in self.group_state.values():
            group.remove()
