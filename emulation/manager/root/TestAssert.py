import logging
import socket
import traceback
import time
from abc import ABCMeta, abstractmethod


ROUTER_PORT = 12000
ROUTER1_IP = '172.16.1.1'
ROUTER2_IP = '172.16.1.2'
ROUTER3_IP = '172.16.1.3'
ROUTER4_IP = '172.16.1.4'
ROUTER5_IP = '172.16.1.5'
ROUTER6_IP = '172.16.1.6'
ROUTER7_IP = '172.16.1.7'
SOURCE_IP = '172.16.1.8'
CLIENT0_IP = '172.16.1.9'
CLIENT1_IP = '172.16.1.10'
MANAGER_IP = '172.16.1.100'

ROUTER1_NAME = "R1"
ROUTER2_NAME = "R2"
ROUTER3_NAME = "R3"
ROUTER4_NAME = "R4"
ROUTER5_NAME = "R5"
ROUTER6_NAME = "R6"
ROUTER7_NAME = "R7"
SOURCE_NAME = "SOURCE"
CLIENT0_NAME = "CLIENT0"
CLIENT1_NAME = "CLIENT1"


class CustomFilter(logging.Filter):
    def filter(self, record):
        return record.name in ("pim.KernelEntry.DownstreamInterface.Assert", "pim.KernelEntry.UpstreamInterface.Assert",
                               "tests") and \
                record.routername in ["R2", "R3", "R4", "R5", "R6", "SOURCE"]


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

    @abstractmethod
    def set_router_state(self):
        pass

    @staticmethod
    def set_initial_settings():
        # format = client_name. client_ip, server_ip
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        msg = "set R1 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER1_IP, ROUTER_PORT))

        msg = "set R2 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER2_IP, ROUTER_PORT))

        msg = "set R3 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER3_IP, ROUTER_PORT))

        msg = "set R4 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER4_IP, ROUTER_PORT))

        msg = "set R5 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER5_IP, ROUTER_PORT))

        msg = "set R6 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER6_IP, ROUTER_PORT))

        msg = "set R7 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (ROUTER7_IP, ROUTER_PORT))

        msg = "set SOURCE {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (SOURCE_IP, ROUTER_PORT))

        msg = "set CLIENT0 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (CLIENT0_IP, ROUTER_PORT))

        msg = "set CLIENT1 {}".format(MANAGER_IP)
        sock.sendto(msg.encode('utf-8'), (CLIENT1_IP, ROUTER_PORT))


    @staticmethod
    def stop_everything():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        msg = "stop"
        sock.sendto(msg.encode('utf-8'), (ROUTER1_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (ROUTER2_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (ROUTER3_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (ROUTER4_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (ROUTER5_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (ROUTER6_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (ROUTER7_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (SOURCE_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (CLIENT0_IP, ROUTER_PORT))
        sock.sendto(msg.encode('utf-8'), (CLIENT1_IP, ROUTER_PORT))


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

    def set_router_state(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (CLIENT0_IP, ROUTER_PORT))
            sock.sendto(msg.encode('utf-8'), (CLIENT1_IP, ROUTER_PORT))

            # INITIAL STATE ROUTER 1
            router_ip = ROUTER1_IP
            router_name = ROUTER1_NAME
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth2"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth2"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth3"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth3"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # INITIAL STATE ROUTER 2
            router_ip = ROUTER2_IP
            router_name = ROUTER2_NAME
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth2"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth2"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # INITIAL STATE ROUTER 3
            router_ip = ROUTER3_IP
            router_name = ROUTER3_NAME
            # CHANGE COST OF eth0 of ROUTER 3 to 10 (initial cost)
            msg = "cost eth0 10"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # INITIAL STATE ROUTER 4
            router_ip = ROUTER4_IP
            router_name = ROUTER4_NAME
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # INITIAL STATE ROUTER 5
            router_ip = ROUTER5_IP
            router_name = ROUTER5_NAME
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # INITIAL STATE ROUTER 6
            router_ip = ROUTER6_IP
            router_name = ROUTER6_NAME
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # INITIAL STATE ROUTER 7
            router_ip = ROUTER7_IP
            router_name = ROUTER7_NAME
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "t {} {}".format(router_name, MANAGER_IP)
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth0"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth1"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "ai eth2"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
            msg = "aiigmp eth2"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            # give time for routers to synchronize
            # and start source
            time.sleep(10)
            msg = "start"
            router_ip = SOURCE_IP
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
        except:
            print(traceback.format_exc())


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

    def set_router_state(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # STOP SOURCE
            router_ip = SOURCE_IP
            msg = "stop"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))

            time.sleep(5)

            # STOP PROCESS AT ROUTER4
            router_ip = ROUTER4_IP
            msg = "stop"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
        except:
            print(traceback.format_exc())


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

    def set_router_state(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # START SOURCE
            router_ip = SOURCE_IP
            msg = "start"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
        except:
            print(traceback.format_exc())


class Test4(Test):
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

        super().__init__("Test4", expectedState, success)

    def print_test(self):
        print("Test4: CouldAssert of AssertWinner(R3) -> False\n" +
              "Change interface eth0 cost of router R3 to 100, causing eth1 to be considered as the Root interface")
        print("Expected: everyone NI")

    def set_router_state(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # CHANGE COST OF eth0 of ROUTER 3 to 100
            router_ip = ROUTER3_IP
            msg = "cost eth0 100"
            sock.sendto(msg.encode('utf-8'), (router_ip, ROUTER_PORT))
        except:
            print(traceback.format_exc())
