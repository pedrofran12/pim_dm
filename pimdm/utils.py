import array, signal, threading, os, sys


def checksum(pkt: bytes) -> bytes:
    if len(pkt) % 2 == 1:
        pkt += "\0"
    s = sum(array.array("H", pkt))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    s = ~s
    return (((s >> 8) & 0xff) | s << 8) & 0xffff


class exit(object):

    status = None

    def __init__(self):
        l = threading.Lock()
        self.acquire = l.acquire
        r = l.release
        def release():
            try:
                if self.status is not None:
                    self.release = r
                    sys.exit(self.status)
            finally:
                r()
        self.release = release

    def __enter__(self):
        self.acquire()

    def __exit__(self, t, v, tb):
        self.release()

    def kill_main(self, status):
        self.status = status
        os.kill(os.getpid(), signal.SIGTERM)

    def signal(self, status, *sigs):
        def handler(*args):
            if self.status is None:
                self.status = status
            if self.acquire(0):
                self.release()
        for sig in sigs:
            signal.signal(sig, handler)

exit = exit()


# obtain TYPE_CHECKING (for type hinting)
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
