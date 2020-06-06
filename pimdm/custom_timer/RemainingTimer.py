from time import time

try:
    from threading import _Timer as Timer
except ImportError:
    from threading import Timer

class RemainingTimer(Timer):
    def __init__(self, interval, function):
        super().__init__(interval, function)
        self.start_time = time()

    def time_remaining(self):
        delta_time = time() - self.start_time
        return self.interval - delta_time


'''
def test():
    print("ola")

x = RemainingTimer(10, test)
x.start()
from time import sleep
for i in range(0, 10):
    print(x.time_remaining())
    sleep(1)
'''
