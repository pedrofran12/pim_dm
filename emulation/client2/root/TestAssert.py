import logging

class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    Rather than use actual contextual information, we just use random
    data in this demo.
    """
    def __init__(self, tree, router_name):
        super().__init__()

    def filter(self, record):
        return record.routername in ["R2","R3","R4","R5","R6"]


class Test1(logging.Filter):
    expectedState = {"R2": "L",
                     "R3": "L",
                     "R4": "W",
                     "R5": "L",
                     "R6": "L",
    }

    Success = {"R2": False,
               "R3": False,
               "R4": False,
               "R5": False,
               "R6": False,
    }

    def __init__(self):
        print("Test1: No info about (10.1.1.100,224.12.12.12)")
        print("Expected: R4 WINNER")
        super().__init__()

    def test(self, record):
        if record.routername not in self.expectedState:
            return False
        if record.msg == self.expectedState.get(record.routername):
            self.Success[record.routername] = True
        if sum(self.Success.values()) == len(self.Success):
            # tudo certo
            print("Test1 Success")
            return True
        return False






class Test2(logging.Filter):
    expectedState = {"R2": "L",
                     "R3": "W",
                     "R5": "L",
                     "R6": "L",
    }

    Success = {"R2": False,
               "R3": False,
               "R5": False,
               "R6": False,
    }

    def __init__(self):
        print("Test2: Kill assert winner")
        print("Expected: R3 WINNER")
        super().__init__()

    def test(self, record):
        if record.routername not in self.expectedState:
            return False
        if record.msg == self.expectedState.get(record.routername):
            self.Success[record.routername] = True
        if sum(self.Success.values()) == len(self.Success):
            # tudo certo
            print("Test2 Success")
            return True
        return False
