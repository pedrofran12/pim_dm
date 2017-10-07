from threading import Timer

class GraftPruneState(object):
    def GraftPruneState(self):
        self._prune_state = SFMRPruneState.DIP
        self._prune_pending_timer = None # type: Timer
        self._prune_timer = None # type: Timer

    def set_prune_pending_timer(self):
        self.clear_prune_pending_timer()
        self._prune_pending_time = Timer()

    def clear_prune_pending_timer(self):
        if self._prune_pending_time is not None:
            self._prune_pending_time.cancel()

    def set_prune_timer(self):
        self.clear_prune_timer()
        self._prune_timer = Timer()

    def clear_prune_timer(self):
        if self._prune_timer is not None:
            self._prune_timer.cancel()
