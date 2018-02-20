import logging

class RootFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    Rather than use actual contextual information, we just use random
    data in this demo.
    """
    def __init__(self, router_name, tree=''):
        super().__init__()
        self.router_name = router_name

    def filter(self, record):
        record.routername = self.router_name
        if not hasattr(record, 'tree'):
            record.tree = ''
        if not hasattr(record, 'vif'):
            record.vif = ''

        return True

class NonRootFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    Rather than use actual contextual information, we just use random
    data in this demo.
    """
    def __init__(self, tree):
        super().__init__()
        self.tree = tree

    def filter(self, record):
        record.tree = self.tree
        return True


class InterfaceFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    Rather than use actual contextual information, we just use random
    data in this demo.
    """
    def __init__(self, vif):
        super().__init__()
        self.vif = vif

    def filter(self, record):
        record.vif = self.vif
        return True
