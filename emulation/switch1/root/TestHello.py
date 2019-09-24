import logging
from abc import ABCMeta, abstractmethod


class CustomFilter(logging.Filter):
    def filter(self, record):
        return record.name in ("pim.Interface.Neighbor", "pim.KernelInterface") and \
                record.routername in ["R1", "R2", "R3", "R4"]


class AddTest(object):
    __metaclass__ = ABCMeta

    def __init__(self, testName, expectedState, success):
        self.testName = testName
        self.expectedState = expectedState
        self.success = success

    def test(self, record):
        if not record.msg.startswith('Monitoring new neighbor') or record.routername not in self.expectedState:
            return False
        if record.neighbor_ip in self.expectedState.get(record.routername).get(record.interfacename):
            self.success[record.routername][record.interfacename][self.expectedState.get(record.routername).get(record.interfacename).index(record.neighbor_ip)] = True

        for interface_test in self.success.values():
            for list_success in interface_test.values():
                if False in list_success:
                    return False
        print('\x1b[1;32;40m' + self.testName + ' Success' + '\x1b[0m')
        return True

    @abstractmethod
    def print_test(self):
        pass


class RemoveTest(object):
    __metaclass__ = ABCMeta

    def __init__(self, testName, expectedState, success):
        self.testName = testName
        self.expectedState = expectedState
        self.success = success

    def test(self, record):
        if not (record.msg.startswith('Detected neighbor removal') or record.msg.startswith('Neighbor Liveness Timer expired')) or record.routername not in self.expectedState:
            return False
        if record.neighbor_ip in self.expectedState.get(record.routername).get(record.interfacename):
            self.success[record.routername][record.interfacename][self.expectedState.get(record.routername).get(record.interfacename).index(record.neighbor_ip)] = True

        for interface_test in self.success.values():
            for list_success in interface_test.values():
                if False in list_success:
                    return False
        print('\x1b[1;32;40m' + self.testName + ' Success' + '\x1b[0m')
        return True

    @abstractmethod
    def print_test(self):
        pass




class Test1(AddTest):
    def __init__(self):
        expectedState = {"R1": {"eth0": ["10.0.0.2", "10.0.0.3", "10.0.0.4"]},
                         "R2": {"eth0": ["10.0.0.1", "10.0.0.3", "10.0.0.4"]},
                         "R3": {"eth0": ["10.0.0.1", "10.0.0.2", "10.0.0.4"]},
                         "R4": {"eth0": ["10.0.0.2", "10.0.0.3", "10.0.0.1"]},
                         }

        success = {"R1": {"eth0": [False, False, False]},
                   "R2": {"eth0": [False, False, False]},
                   "R3": {"eth0": [False, False, False]},
                   "R4": {"eth0": [False, False, False]},
                   }

        super().__init__("Test1", expectedState, success)

    def print_test(self):
        print("Test1: Enable all routers")
        print("All routers should establish neighborhood relationships")


class Test2(RemoveTest):
    def __init__(self):
        expectedState = {"R1": {"eth0": ["10.0.0.3"]},
                         "R2": {"eth0": ["10.0.0.3"]},
                         "R4": {"eth0": ["10.0.0.3"]},
                         }

        success = {"R1": {"eth0": [False]},
                   "R2": {"eth0": [False]},
                   "R4": {"eth0": [False]},
                   }

        super().__init__("Test2", expectedState, success)

    def print_test(self):
        print("Test2: Disable Router3 interface (-ri eth0) and check if others router react to R3 HelloHoldTime=0")


class Test3(RemoveTest):
    def __init__(self):
        expectedState = {"R1": {"eth0": ["10.0.0.4"]},
                         "R2": {"eth0": ["10.0.0.4"]},
                         }

        success = {"R1": {"eth0": [False]},
                   "R2": {"eth0": [False]},
                   }

        super().__init__("Test3", expectedState, success)

    def print_test(self):
        print("Test3: KILL router4 (-stop) to not send Hello with HelloHoldTime set to 0 and check if others remove that router after timeout")

class Test4(AddTest):
    def __init__(self):
        expectedState = {"R1": {"eth0": ["10.0.0.4"]},
                         "R2": {"eth0": ["10.0.0.4"]},
                         "R4": {"eth0": ["10.0.0.2", "10.0.0.1"]},
                         }

        success = {"R1": {"eth0": [False]},
                   "R2": {"eth0": [False]},
                   "R4": {"eth0": [False, False]},
                   }

        super().__init__("Test4", expectedState, success)

    def print_test(self):
        print("Test4: Reenable router4")
