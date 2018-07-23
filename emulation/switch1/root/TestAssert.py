import logging
from abc import ABCMeta, abstractmethod


class CustomFilter(logging.Filter):
    def filter(self, record):
        return record.name in ("pim.KernelEntry.DownstreamInterface.Assert", "pim.KernelEntry.UpstreamInterface.Assert") and \
                record.routername in ["R2", "R3", "R4", "R5", "R6"]


class Test(object):
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
                return False
        print('\x1b[1;32;40m' + self.testName + ' Success' + '\x1b[0m')
        return True

    @abstractmethod
    def print_test(self):
        pass


class Test1(Test):
    def __init__(self):
        expectedState = {"R2": {"eth1": "Assert state transitions to Loser"},
                         "R3": {"eth1": "Assert state transitions to Loser"},
                         "R4": {"eth1": "Assert state transitions to Winner"},
                         "R5": {"eth0": "Assert state transitions to Loser"},
                         "R6": {"eth0": "Assert state transitions to Loser"},
                         }

        success = {"R2": {"eth1": False},
                   "R3": {"eth1": False},
                   "R4": {"eth1": False},
                   "R5": {"eth0": False},
                   "R6": {"eth0": False},
                   }

        super().__init__("Test1", expectedState, success)

    def print_test(self):
        print("Test1: No info about (10.1.1.100,224.12.12.12) and data packets are flooded on the network")
        print("Expected: R4 WINNER")


class Test2(Test):
    def __init__(self):
        expectedState = {"R2": {"eth1": "Assert state transitions to NoInfo"},
                         "R3": {"eth1": "Assert state transitions to NoInfo"},
                         "R5": {"eth0": "Assert state transitions to NoInfo"},
                         "R6": {"eth0": "Assert state transitions to NoInfo"},
                         }

        success = {"R2": {"eth1": False},
                   "R3": {"eth1": False},
                   "R5": {"eth0": False},
                   "R6": {"eth0": False},
                   }
        super().__init__("Test2", expectedState, success)

    def print_test(self):
        print("Test2: Kill Assert Winner and dont send data packets")
        print("Expected: Every AL transitions to NI")


class Test3(Test):
    def __init__(self):
        expectedState = {"R2": {"eth1": "Assert state transitions to Loser"},
                         "R3": {"eth1": "Assert state transitions to Winner"},
                         "R5": {"eth0": "Assert state transitions to Loser"},
                         "R6": {"eth0": "Assert state transitions to Loser"},
                         }

        success = {"R2": {"eth1": False},
                   "R3": {"eth1": False},
                   "R5": {"eth0": False},
                   "R6": {"eth0": False},
                   }
        super().__init__("Test3", expectedState, success)

    def print_test(self):
        print("Test3: Source sends data causing the reelection of AW")
        print("Expected: R3 WINNER")


class Test4(Test):
    def __init__(self):
        expectedState = {"R2": {"eth1": "Assert state transitions to NoInfo"},
                         "R3": {"eth1": "Assert state transitions to NoInfo"},
                         }

        success = {"R2": {"eth1": False},
                   "R3": {"eth1": False},
                   }

        super().__init__("Test4", expectedState, success)

    def print_test(self):
        print("Test4: CouldAssert of AssertWinner(R3) -> False\n" + 
	      "Change interface eth0 cost of router R3 to 100, causing eth1 to be considered as the Root interface")
        print("Expected: everyone NI")

