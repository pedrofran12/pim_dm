import logging
from abc import ABCMeta

class CustomFilter(logging.Filter):
    def filter(self, record):
        return record.name in ("pim.KernelEntry.DownstreamInterface.JoinPrune", "pim.KernelEntry.UpstreamInterface.JoinPrune", "pim.KernelInterface") and \
                record.routername in ["R1", "R2","R3","R4","R5","R6"]


class Test():
    __metaclass__ = ABCMeta

    def __init__(self, testName, expectedState, success):
        self.testName = testName
        self.expectedState = expectedState
        self.success = success

    def test(self, record):
        if record.routername not in self.expectedState:
            return False
        if record.msg == self.expectedState.get(record.routername).get(record.interfacename):
            self.success[record.routername][record.interfacename] = True

        for interface_test in self.success.values():
            if False in interface_test.values():
                #print(self.expectedState)
                #print(self.success)
                return False
        print('\x1b[1;32;40m' + self.testName + ' Success' + '\x1b[0m')
        return True




class Test1(Test):

    def __init__(self):
        expectedState = {"R1": {"eth0": "F", "eth1": "P", "eth2": "P", "eth3": "NI"}, # Only downstream interface connected to AssertWinner \
                                                                                      # in NI state and upstream interface connected to source\
                                                                                      # in Forward state
                         "R2": {"eth0": "P"}, # Assert Loser upstream interface in pruned state
                         "R3": {"eth0": "P"}, # Assert Loser upstream interface in pruned state
                         "R4": {"eth0": "F", "eth1": "NI"}, # Assert Winner upstream interface in forward state
                         "R5": {"eth0": "F"}, # Downstream router interested (client0)
                         "R6": {"eth0": "F"}, # Downstream router interested (client0)
                         }

        success = {"R1": {"eth0": False, "eth1": False, "eth2": False, "eth3": False},
                   "R2": {"eth0": False},
                   "R3": {"eth0": False},
                   "R4": {"eth0": False, "eth1": False},
                   "R5": {"eth0": False},
                   "R6": {"eth0": False},
                   }

        super().__init__("Test1", expectedState, success)

    def print_test(self):
        print("Test1: Formation of (S,G) Broadcast Tree")
        print("Having Client0 and Client1 interested")



class Test2(Test):
    def __init__(self):
        expectedState = {"R4": {"eth1": "PP"}, # Assert Winner upstream interface in PP because of Prune msg
                         "R6": {"eth0": "P"}, # Downstream router not interested
                         }

        success = {"R4": {"eth1": False},
                   "R6": {"eth0": False},
                   }
        super().__init__("Test2", expectedState, success)

    def print_test(self):
        print("Test2: Client1 not interested in receiving traffic destined to group G")
        print("R6 sends a Prune and R5 overrides the prune")


class Test3(Test):
    def __init__(self):
        expectedState = {"R4": {"eth1": "NI"}, # Assert Winner upstream interface in PP because of Join msg
                         }

        success = {"R4": {"eth1": False},
                   }

        super().__init__("Test3", expectedState, success)

    def print_test(self):
        print("Test3: R5 overrides prune via Join")
        print("R4 should transition to Forward state")


class Test4(Test):
    def __init__(self):

        expectedState = {"R1": {"eth3": "P"}, # Only interface eth3 changes to Pruned state... eth1 is directly connected so it should stay in a Forward state
                         #"R2": {"eth0": "P"}, #R2 already in a Pruned state
                         #"R3": {"eth0": "P"}, #R3 already in a Pruned state
                         "R4": {"eth0": "P", "eth1": "P"}, # Assert Winner upstream interface in forward state
                         "R5": {"eth0": "P"}, # Downstream router interested (client0)
                         #"R6": {"eth0": "P"}, # R6 already in a Pruned state
                         }

        success = {"R1": {"eth3": False},
                   "R4": {"eth0": False, "eth1": False},
                   "R5": {"eth0": False},
                   }

        super().__init__("Test4", expectedState, success)

    def print_test(self):
        print("Test4: No client interested")
        print("Prune tree")


class Test5(Test):
    def __init__(self):

        expectedState = {"R1": {"eth3": "NI"}, # R4 grafted this interface
                         "R4": {"eth0": "F", "eth1": "NI"}, # R5 grafted this interface
                         "R5": {"eth0": "F"}, # client0 interested
                         }

        success = {"R1": {"eth3": False},
                   "R4": {"eth0": False, "eth1": False},
                   "R5": {"eth0": False},
                   }

        super().__init__("Test5", expectedState, success)

    def print_test(self):
        print("Test5: client0 interested in receiving traffic")
        print("Graft tree")
