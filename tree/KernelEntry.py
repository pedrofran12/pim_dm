from tree.tree_if_upstream import TreeInterfaceUpstream
from tree.tree_if_downstream import TreeInterfaceDownstream
from .tree_interface import TreeInterface
from threading import Timer, Lock, RLock
from tree.metric import AssertMetric
import UnicastRouting
from time import time
import Main
import logging

class KernelEntry:
    TREE_TIMEOUT = 180
    KERNEL_LOGGER = logging.getLogger('pim.KernelEntry')

    def __init__(self, source_ip: str, group_ip: str):
        self.kernel_entry_logger = logging.LoggerAdapter(KernelEntry.KERNEL_LOGGER, {'tree': '(' + source_ip + ',' + group_ip + ')'})
        self.kernel_entry_logger.debug('Create KernelEntry')

        self.source_ip = source_ip
        self.group_ip = group_ip

        # ip of neighbor of the rpf
        #next_hop = UnicastRouting.get_route(source_ip)["gateway"]
        #self.rpf_node = source_ip if next_hop is None else next_hop

        '''
        next_hop = UnicastRouting.get_route(source_ip)["gateway"]
        multipaths = UnicastRouting.get_route(source_ip)["multipath"]

        self.rpf_node = next_hop if next_hop is not None else source_ip
        print("MUL", multipaths)
        #self.rpf_node = multipaths[0]["gateway"]
        for m in multipaths:
            if m["gateway"] is None:
                self.rpf_node = source_ip
                break
            else:
                self.rpf_node = m["gateway"]
        '''
        unicast_route = UnicastRouting.get_route(source_ip)
        next_hop = unicast_route["gateway"]
        multipaths = unicast_route["multipath"]

        self.rpf_node = next_hop if next_hop is not None else source_ip
        import ipaddress
        highest_ip = ipaddress.ip_address("0.0.0.0")
        for m in multipaths:
            if m["gateway"] is None:
                self.rpf_node = source_ip
                break
            elif ipaddress.ip_address(m["gateway"]) > highest_ip:
                highest_ip = ipaddress.ip_address(m["gateway"])
                self.rpf_node = m["gateway"]

        print("RPF_NODE:", UnicastRouting.get_route(source_ip))
        print(self.rpf_node == source_ip)

        # (S,G) starts IG state
        self._was_olist_null = False

        # Locks
        self._multicast_change = Lock()
        self._lock_test2 = RLock()
        self.CHANGE_STATE_LOCK = RLock()

        # decide inbound interface based on rpf check
        self.inbound_interface_index = Main.kernel.vif_dic[self.check_rpf()]

        self.interface_state = {}  # type: Dict[int, TreeInterface]
        with self.CHANGE_STATE_LOCK:
            for i in Main.kernel.vif_index_to_name_dic.keys():
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

        #self._lock = threading.RLock()


    def get_inbound_interface_index(self):
        return self.inbound_interface_index

    def get_outbound_interfaces_indexes(self):
        outbound_indexes = [0]*Main.kernel.MAXVIFS
        for (index, state) in self.interface_state.items():
            outbound_indexes[index] = state.is_forwarding()
        return outbound_indexes

    def check_rpf(self):
        return UnicastRouting.check_rpf(self.source_ip)


    ################################################
    # Receive (S,G) data packets or control packets
    ################################################
    def recv_data_msg(self, index):
        print("recv data")
        self.interface_state[index].recv_data_msg()

    def recv_assert_msg(self, index, packet):
        print("recv assert")
        pkt_assert = packet.payload.payload
        metric = pkt_assert.metric
        metric_preference = pkt_assert.metric_preference
        assert_sender_ip = packet.ip_header.ip_src

        received_metric = AssertMetric(metric_preference=metric_preference, route_metric=metric, ip_address=assert_sender_ip)
        self.interface_state[index].recv_assert_msg(received_metric)

    def recv_prune_msg(self, index, packet):
        print("recv prune msg")
        holdtime = packet.payload.payload.hold_time
        upstream_neighbor_address = packet.payload.payload.upstream_neighbor_address
        self.interface_state[index].recv_prune_msg(upstream_neighbor_address=upstream_neighbor_address, holdtime=holdtime)

    def recv_join_msg(self, index, packet):
        print("recv join msg")
        upstream_neighbor_address = packet.payload.payload.upstream_neighbor_address
        self.interface_state[index].recv_join_msg(upstream_neighbor_address)

    def recv_graft_msg(self, index, packet):
        print("recv graft msg")
        upstream_neighbor_address = packet.payload.payload.upstream_neighbor_address
        source_ip = packet.ip_header.ip_src
        self.interface_state[index].recv_graft_msg(upstream_neighbor_address, source_ip)

    def recv_graft_ack_msg(self, index, packet):
        print("recv graft ack msg")
        source_ip = packet.ip_header.ip_src
        self.interface_state[index].recv_graft_ack_msg(source_ip)

    def recv_state_refresh_msg(self, index, packet):
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
        if (timestamp - self.timestamp_of_last_state_refresh_message_received) < interval:
            return
        self.timestamp_of_last_state_refresh_message_received = timestamp
        if ttl == 0:
            return

        self.forward_state_refresh_msg(packet.payload.payload)


    ################################################
    # Send state refresh msg
    ################################################
    def forward_state_refresh_msg(self, state_refresh_packet):
        for interface in self.interface_state.values():
            interface.send_state_refresh(state_refresh_packet)


    ###############################################################
    # Unicast Changes to RPF
    ###############################################################
    def network_update(self):
        # TODO TALVEZ OUTRO LOCK PARA BLOQUEAR ENTRADA DE PACOTES
        with self.CHANGE_STATE_LOCK:
            '''
            next_hop = UnicastRouting.get_route(self.source_ip)["gateway"]
            multipaths = UnicastRouting.get_route(self.source_ip)["multipath"]

            rpf_node = next_hop
            print("MUL", multipaths)
            # self.rpf_node = multipaths[0]["gateway"]
            for m in multipaths:
                if m["gateway"] is None:
                    rpf_node = self.source_ip
                    break
                else:
                    rpf_node = m["gateway"]
            '''
            unicast_route = UnicastRouting.get_route(self.source_ip)
            next_hop = unicast_route["gateway"]
            multipaths = unicast_route["multipath"]

            rpf_node = next_hop if next_hop is not None else self.source_ip
            import ipaddress
            highest_ip = ipaddress.ip_address("0.0.0.0")
            for m in multipaths:
                if m["gateway"] is None:
                    rpf_node = self.source_ip
                    break
                elif ipaddress.ip_address(m["gateway"]) > highest_ip:
                    highest_ip = ipaddress.ip_address(m["gateway"])
                    rpf_node = m["gateway"]

            print("RPF_NODE:", UnicastRouting.get_route(self.source_ip))


            print(self.rpf_node == self.source_ip)

            new_inbound_interface_index = Main.kernel.vif_dic.get(self.check_rpf(), None)
            if new_inbound_interface_index is None:
                self.delete()
                return
            if new_inbound_interface_index != self.inbound_interface_index:
                self.rpf_node = rpf_node

                # get old interfaces
                old_upstream_interface = self.interface_state[self.inbound_interface_index]
                old_downstream_interface = self.interface_state[new_inbound_interface_index]

                # change type of interfaces
                new_downstream_interface = TreeInterfaceDownstream(self, self.inbound_interface_index)
                self.interface_state[self.inbound_interface_index] = new_downstream_interface
                new_upstream_interface = TreeInterfaceUpstream(self, new_inbound_interface_index)
                self.interface_state[new_inbound_interface_index] = new_upstream_interface
                self.inbound_interface_index = new_inbound_interface_index

                # remove old interfaces
                old_upstream_interface.delete(change_type_interface=True)
                old_downstream_interface.delete(change_type_interface=True)

                # atualizar tabela de encaminhamento multicast
                #self._was_olist_null = False
                self.change()
                self.evaluate_olist_change()
                new_upstream_interface.change_on_unicast_routing(interface_change=True)
            elif self.rpf_node != rpf_node:
                self.rpf_node = rpf_node
                self.interface_state[self.inbound_interface_index].change_on_unicast_routing()


    # check if add/removal of neighbors from interface afects olist and forward/prune state of interface
    def change_at_number_of_neighbors(self):
        with self.CHANGE_STATE_LOCK:
            self.change()
            self.evaluate_olist_change()

    def new_or_reset_neighbor(self, if_index, neighbor_ip):
        # todo maybe lock de interfaces
        self.interface_state[if_index].new_or_reset_neighbor(neighbor_ip)

    def is_olist_null(self):
        for interface in self.interface_state.values():
            if interface.is_forwarding():
                return False
        return True

    def evaluate_olist_change(self):
        with self._lock_test2:
            is_olist_null = self.is_olist_null()

            if self._was_olist_null != is_olist_null:
                if is_olist_null:
                    self.interface_state[self.inbound_interface_index].olist_is_null()
                else:
                    self.interface_state[self.inbound_interface_index].olist_is_not_null()

                self._was_olist_null = is_olist_null

    def get_source(self):
        return self.source_ip

    def get_group(self):
        return self.group_ip

    def change(self):
        with self._multicast_change:
            Main.kernel.set_multicast_route(self)

    def delete(self):
        with self._multicast_change:
            for state in self.interface_state.values():
                state.delete()

            Main.kernel.remove_multicast_route(self)


    ######################################
    # Interface change
    #######################################
    def new_interface(self, index):
        with self.CHANGE_STATE_LOCK:
            self.interface_state[index] = TreeInterfaceDownstream(self, index)
            self.change()
            self.evaluate_olist_change()

    def remove_interface(self, index):
        with self.CHANGE_STATE_LOCK:
            #check if removed interface is root interface
            if self.inbound_interface_index == index:
                self.delete()
            else:
                self.interface_state.pop(index).delete()
                self.change()
                self.evaluate_olist_change()
