import logging
from abc import ABCMeta

class CustomFilter(logging.Filter):
    def filter(self, record):
        return record.name in ("pim.KernelEntry.UpstreamInterface.Originator",
                               "pim.KernelEntry.DownstreamInterface.JoinPrune",
                               "pim.KernelEntry.UpstreamInterface.JoinPrune",
                               "pim.KernelInterface",
                               "pim.KernelEntry.DownstreamInterface.Assert",
                               "pim.KernelEntry.UpstreamInterface.Assert") and\
                record.routername in ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]


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
        expectedState = {"R1": {"eth0": "StateRefresh state transitions to Originator"},
                         "R2": {"eth0": "StateRefresh state transitions to NotOriginator"},
                         "R3": {"eth0": "StateRefresh state transitions to NotOriginator"},
                         "R4": {"eth0": "StateRefresh state transitions to NotOriginator"},
                         "R5": {"eth0": "StateRefresh state transitions to NotOriginator"},
                         "R6": {"eth0": "StateRefresh state transitions to NotOriginator"},
                         "R7": {"eth0": "StateRefresh state transitions to NotOriginator"},
                         }

        success = {"R1": {"eth0": False},
                   "R2": {"eth0": False},
                   "R3": {"eth0": False},
                   "R4": {"eth0": False},
                   "R5": {"eth0": False},
                   "R6": {"eth0": False},
                   "R7": {"eth0": False},
                   }

        super().__init__("Test1", expectedState, success)

    def print_test(self):
        print("Test1: Originator")
        print("Having Client0 and Client1 interested")


class Test2(Test):
    def __init__(self):
        expectedState = {"R1": {"eth0": "StateRefresh state transitions to NotOriginator"}
                         }

        success = {"R1": {"eth0": False},
                   }
        super().__init__("Test2", expectedState, success)

    def print_test(self):
        print("Test2: After some time without source sending data... router originator should transition to NO")


class Test3(Test):
    def __init__(self):
        expectedState = {"R1": {"eth0": "StateRefresh state transitions to Originator"}
                         }

        success = {"R1": {"eth0": False},
                   }
        super().__init__("Test3", expectedState, success)

    def print_test(self):
        print("Test3: Source sends data")
        print("Expected: R1 transitions to Originator")
