from threading import Timer

class OriginatorState(object):
    def OriginatorState(self):
        self._source_active_timer = None # type: Timer
        self._state_refresh_timer = None # type: Timer

    def set_source_active_timer(self):
        self.clear_source_active_timer()
        self._source_active_timer = Timer()

    def clear_source_active_timer(self):
        if self._source_active_timer is not None:
            self._source_active_timer.cancel()

    def set_state_refresh_timer(self):
        self.clear_state_refresh_timer()
        self._state_refresh_timer = Timer()

    def clear_state_refresh_timer(self):
        if self._state_refresh_timer is not None:
            self._state_refresh_timer.cancel()
