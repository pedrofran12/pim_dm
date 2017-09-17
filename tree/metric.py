'''
Created on Jul 20, 2015

@author: alex
'''
import ipaddress


class SFMRAssertMetric(object):
    '''
    Note: we consider the node name the ip of the metric.
    '''

    def __init__(self, metric_preference: int or float, route_metric: int or float, ip_address: str):
        if type(ip_address) is str:
            ip_address = ipaddress.ip_address(ip_address)

        self._metric_preference = metric_preference
        self._route_metric = route_metric
        self._ip_address = ip_address

    def is_worse_than(self, other):
        assert isinstance(other, SFMRAssertMetric)

        if self.get_metric_preference() != other.get_metric_preference():
            return self.get_metric_preference() > other.get_metric_preference()
        elif self.get_route_metric() != other.get_route_metric():
            return self.get_route_metric() > other.get_route_metric()
        else:
            return self.get_ip_address() <= other.get_ip_address()

    @staticmethod
    def infinite_assert_metric():
        '''
        @rtype SFMRAssertMetric
        @type tree_if: SFRMTreeInterface
        '''
        #metric = SFMRAssertMetric()

        #metric._metric = float("Inf")
        #metric._node = ""

        metric_preference = float("Inf")
        route_metric = float("Inf")
        ip = "0.0.0.0"
        metric = SFMRAssertMetric(metric_preference=metric_preference, route_metric=route_metric, ip_address=ip)
        return metric

    @staticmethod
    def spt_assert_metric(tree_if):
        '''
        @rtype SFMRAssertMetric
        @type tree_if: SFRMTreeInterface
        '''
        #metric = SFMRAssertMetric()

        #metric._metric = tree_if.get_cost()
        #metric._node = tree_if.get_node()


        metric_preference = 10 # todo check how to get metric preference
        route_metric = tree_if.get_cost()
        ip = tree_if.get_ip()
        metric = SFMRAssertMetric(metric_preference=metric_preference, route_metric=route_metric, ip_address=ip)

        return metric

    # overrides
    #def __str__(self):
    #    return "AssertMetric<%d:%d:%s>" % (self._metric_preference, self._node)

    def get_metric_preference(self):
        return self._metric_preference

    def get_route_metric(self):
        return self._route_metric

    def get_ip_address(self):
        return self._ip_address

    def set_metric_preference(self, metric_preference):
        self._metric_preference = metric_preference

    def set_route_metric(self, route_metric):
        self._route_metric = route_metric

    def set_ip_address(self, ip):
        self._ip_address = ip
