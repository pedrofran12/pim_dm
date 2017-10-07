from threading import Timer

class PruneState(object):
    def PruneState(self):
        self._prune_state = SFMRPruneState.DIP
        self._prune_pending_timer = None
        self._prune_timer = None

    def set_prune_pending_timer(self):
        self.clear_prune_pending_timer()
        self._prune_pending_timer= Timer()

    def clear_prune_pending_timer(self):
        if self._prune_pending_timer is not None:
            self._prune_pending_timer.cancel()

    def set_prune_timer(self):
        self.clear_prune_timer()
        self._prune_timer= Timer()

    def clear_prune_timer(self):
        if self._prune_timer is not None:
            self._prune_timer.cancel()
