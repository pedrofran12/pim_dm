import logging
from time import time
from threading import Lock, RLock

from pimdm import UnicastRouting
from .metric import AssertMetric
from .tree_if_upstream import TreeInterfaceUpstream
from .tree_if_downstream import TreeInterfaceDownstream
from .tree_interface import TreeInterface


class KernelEntry:
    KERNEL_LOGGER = logging.getLogger('pim.KernelEntry')

    def __init__(self, source_ip: str, group_ip: str, kernel_entry_interface):
        self.kernel_entry_logger = logging.LoggerAdapter(KernelEntry.KERNEL_LOGGER,
                                                         {'tree': '(' + source_ip + ',' + group_ip + ')'})
        self.kernel_entry_logger.debug('Create KernelEntry')

        self.source_ip = source_ip
        self.group_ip = group_ip

        self._kernel_entry_interface = kernel_entry_interface

        # OBTAIN UNICAST ROUTING INFORMATION###################################################
        (metric_administrative_distance, metric_cost, rpf_node, root_if, mask) = \
            UnicastRouting.get_unicast_info(source_ip)
        if root_if is None:
            raise Exception
        self.rpf_node = rpf_node

        # (S,G) starts IG state
        self._was_olist_null = False

        # Locks
        self._multicast_change = Lock()
        self._lock_test2 = RLock()
        self.CHANGE_STATE_LOCK = RLock()

        # decide inbound interface based on rpf check
        self.inbound_interface_index = root_if

        self.interface_state = {}  # type: Dict[int, TreeInterface]
        with self.CHANGE_STATE_LOCK:
            for i in self.get_kernel().vif_index_to_name_dic.keys():
                try:
                    if i == self.inbound_interface_index:
                        self.interface_state[i] = TreeInterfaceUpstream(self, i)
                    else:
                        self.interface_state[i] = TreeInterfaceDownstream(self, i)
                except:
                    import traceback
                    print(traceback.print_exc())
                    continue

        self.change()
        self.evaluate_olist_change()
        self.timestamp_of_last_state_refresh_message_received = 0
        print('Tree created')

    def get_inbound_interface_index(self):
        """
        Get VIF of root interface of this tree
        """
        return self.inbound_interface_index

    def get_outbound_interfaces_indexes(self):
        """
        Get OIL of this tree
        """
        return self._kernel_entry_interface.get_outbound_interfaces_indexes(self)

    ################################################
    # Receive (S,G) data packets or control packets
    ################################################
    def recv_data_msg(self, index):
        """
        Receive data packet regarding this tree in interface with VIF index
        """
        print("recv data")
        self.interface_state[index].recv_data_msg()

    def recv_assert_msg(self, index, packet):
        """
        Receive assert packet regarding this tree in interface with VIF index
        """
        print("recv assert")
        pkt_assert = packet.payload.payload
        metric = pkt_assert.metric
        metric_preference = pkt_assert.metric_preference
        assert_sender_ip = packet.ip_header.ip_src

        received_metric = AssertMetric(metric_preference=metric_preference, route_metric=metric, ip_address=assert_sender_ip)
        self.interface_state[index].recv_assert_msg(received_metric)

    def recv_prune_msg(self, index, packet):
        """
        Receive Prune packet regarding this tree in interface with VIF index
        """
        print("recv prune msg")
        holdtime = packet.payload.payload.hold_time
        upstream_neighbor_address = packet.payload.payload.upstream_neighbor_address
        self.interface_state[index].recv_prune_msg(upstream_neighbor_address=upstream_neighbor_address, holdtime=holdtime)

    def recv_join_msg(self, index, packet):
        """
        Receive Join packet regarding this tree in interface with VIF index
        """
        print("recv join msg")
        upstream_neighbor_address = packet.payload.payload.upstream_neighbor_address
        self.interface_state[index].recv_join_msg(upstream_neighbor_address)

    def recv_graft_msg(self, index, packet):
        """
        Receive Graft packet regarding this tree in interface with VIF index
        """
        print("recv graft msg")
        upstream_neighbor_address = packet.payload.payload.upstream_neighbor_address
        source_ip = packet.ip_header.ip_src
        self.interface_state[index].recv_graft_msg(upstream_neighbor_address, source_ip)

    def recv_graft_ack_msg(self, index, packet):
        """
        Receive GraftAck packet regarding this tree in interface with VIF index
        """
        print("recv graft ack msg")
        source_ip = packet.ip_header.ip_src
        self.interface_state[index].recv_graft_ack_msg(source_ip)

    def recv_state_refresh_msg(self, index, packet):
        """
        Receive StateRefresh packet regarding this tree in interface with VIF index
        """
        print("recv state refresh msg")
        source_of_state_refresh = packet.ip_header.ip_src

        metric_preference = packet.payload.payload.metric_preference
        metric = packet.payload.payload.metric
        ttl = packet.payload.payload.ttl
        prune_indicator_flag = packet.payload.payload.prune_indicator_flag #P
        interval = packet.payload.payload.interval
        received_metric = AssertMetric(metric_preference=metric_preference, route_metric=metric, ip_address=source_of_state_refresh, state_refresh_interval=interval)
        self.interface_state[index].recv_state_refresh_msg(received_metric, prune_indicator_flag)

        iif = packet.interface.vif_index
        if iif != self.inbound_interface_index:
            return
        if self.interface_state[iif].get_neighbor_RPF() != source_of_state_refresh:
            return
        # refresh limit
        timestamp = time()
        if (timestamp - self.timestamp_of_last_state_refresh_message_received) < interval - 5:
            return
        self.timestamp_of_last_state_refresh_message_received = timestamp
        if ttl == 0:
            return

        self.forward_state_refresh_msg(packet.payload.payload)

    ################################################
    # Send state refresh msg
    ################################################
    def forward_state_refresh_msg(self, state_refresh_packet):
        """
        Forward StateRefresh packet through all interfaces
        """
        for interface in self.interface_state.values():
            interface.send_state_refresh(state_refresh_packet)


    ###############################################################
    # Unicast Changes to RPF
    ###############################################################
    def network_update(self):
        """
        Unicast routing table suffered an update and this tree might be affected by it
        """
        # TODO TALVEZ OUTRO LOCK PARA BLOQUEAR ENTRADA DE PACOTES
        with self.CHANGE_STATE_LOCK:

            (metric_administrative_distance, metric_cost, rpf_node, new_inbound_interface_index, _) = \
                UnicastRouting.get_unicast_info(self.source_ip)

            if new_inbound_interface_index is None:
                self.delete()
                return
            if new_inbound_interface_index != self.inbound_interface_index:
                self.rpf_node = rpf_node

                # get old interfaces
                old_upstream_interface = self.interface_state.get(self.inbound_interface_index, None)
                old_downstream_interface = self.interface_state.get(new_inbound_interface_index, None)

                # change type of interfaces
                if self.inbound_interface_index is not None:
                    new_downstream_interface = TreeInterfaceDownstream(self, self.inbound_interface_index)
                    self.interface_state[self.inbound_interface_index] = new_downstream_interface
                new_upstream_interface = None
                if new_inbound_interface_index is not None:
                    new_upstream_interface = TreeInterfaceUpstream(self, new_inbound_interface_index)
                    self.interface_state[new_inbound_interface_index] = new_upstream_interface
                self.inbound_interface_index = new_inbound_interface_index

                # remove old interfaces
                if old_upstream_interface is not None:
                    old_upstream_interface.delete(change_type_interface=True)
                if old_downstream_interface is not None:
                    old_downstream_interface.delete(change_type_interface=True)

                # atualizar tabela de encaminhamento multicast
                #self._was_olist_null = False
                self.change()
                self.evaluate_olist_change()
                if new_upstream_interface is not None:
                    new_upstream_interface.change_on_unicast_routing(interface_change=True)
            elif self.rpf_node != rpf_node:
                self.rpf_node = rpf_node
                self.interface_state[self.inbound_interface_index].change_on_unicast_routing()

    def change_at_number_of_neighbors(self):
        """
        Check if modification of number of neighbors causes changes to OIL and interest of interface
        """
        with self.CHANGE_STATE_LOCK:
            self.change()
            self.evaluate_olist_change()

    def new_or_reset_neighbor(self, if_index, neighbor_ip):
        """
        An interface identified by if_index has a new neighbor
        """
        # todo maybe lock de interfaces
        self.interface_state[if_index].new_or_reset_neighbor(neighbor_ip)

    def is_olist_null(self):
        """
        Check if olist is null
        """
        for interface in self.interface_state.values():
            if interface.is_forwarding():
                return False
        return True

    def evaluate_olist_change(self):
        """
        React to changes on the olist
        """
        with self._lock_test2:
            is_olist_null = self.is_olist_null()

            if self._was_olist_null != is_olist_null:
                if is_olist_null:
                    self.interface_state[self.inbound_interface_index].olist_is_null()
                else:
                    self.interface_state[self.inbound_interface_index].olist_is_not_null()

                self._was_olist_null = is_olist_null

    def get_source(self):
        """
        Get source IP of multicast source
        """
        return self.source_ip

    def get_group(self):
        """
        Get group IP of multicast tree
        """
        return self.group_ip

    def change(self):
        """
        Trigger an update on the multicast routing table
        """
        with self._multicast_change:
            self.get_kernel().set_multicast_route(self)

    def delete(self):
        """
        Remove kernel entry
        """
        with self._multicast_change:
            for state in self.interface_state.values():
                state.delete()

            self.get_kernel().remove_multicast_route(self)

    def get_interface_name(self, interface_id):
        """
        Get interface name of interface identified by interface_id
        """
        return self._kernel_entry_interface.get_interface_name(interface_id)

    def get_interface(self, interface_id):
        """
        Get PIM interface
        """
        return self._kernel_entry_interface.get_interface(self, interface_id)

    def get_membership_interface(self, interface_id):
        """
        Get IGMP/MLD interface
        """
        return self._kernel_entry_interface.get_membership_interface(self, interface_id)

    def get_kernel(self):
        """
        Get kernel
        """
        return self._kernel_entry_interface.get_kernel()

    ######################################
    # Interface change
    #######################################
    def new_interface(self, index):
        """
        React to a new interface that was added and in which a tree was already built
        """
        with self.CHANGE_STATE_LOCK:
            self.interface_state[index] = TreeInterfaceDownstream(self, index)
            self.change()
            self.evaluate_olist_change()

    def remove_interface(self, index):
        """
        React to removal of an interface of a tree that was already built
        """
        with self.CHANGE_STATE_LOCK:
            #check if removed interface is root interface
            if self.inbound_interface_index == index:
                self.delete()
            elif index in self.interface_state:
                self.interface_state.pop(index).delete()
                self.change()
                self.evaluate_olist_change()
