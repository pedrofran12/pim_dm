'''
Created on Sep 8, 2014

@author: alex
'''


class AssertMetric(object):
    '''
    Note: we consider the node name the ip of the metric.
    '''

    def __init__(self):
        '''
         @type tree_if: TreeInterface
        '''
        self._pref = None
        self._metric = None
        self._node = None

    def is_worse_than(self, other):
        if self._pref != other.pref:
            return self._pref > other.pref

        elif self._metric != other.metric:
            return self._metric > other.metric

        else:
            return self._node.__str__() <= other.node.__str__()

    @property
    def pref(self):
        return self._pref

    @property
    def metric(self):
        return self._metric

    @property
    def node(self):
        return self._node

    @staticmethod
    def infinite_assert_metric():
        '''
        @type metric: AssertMetric
        '''
        metric = AssertMetric()

        metric._pref = 1
        metric._metric = float("Inf")
        metric._node = ""

        return metric

    @staticmethod
    def spt_assert_metric(tree_if):
        '''
        @type metric: AssertMetric
        @type tree_if: TreeInterface
        '''
        metric = AssertMetric()

        metric._pref = 1  # TODO: ver isto melhor no route preference
        metric._metric = tree_if.metric
        metric._node = tree_if.node

        return metric

    # overrides
    def __str__(self):
        return "AssertMetric<{}:{}:{}>".format(self._pref, self._metric,
                                               self._node)
