from threading import Timer

class AssertWinnerState(object):
    def GraftPruneState(self):
        self._assert_state = AssertState.Winner
        self._assert_timer = None
        self._assert_winner_ip = None
        self._assert_winner_metric = None

    def set_assert_timer(self):
        self.clear_assert_timer()
        self._assert_timer= Timer()

    def clear_assert_timer(self):
        if self._assert_timer is not None:
            self._assert_timer.cancel()
