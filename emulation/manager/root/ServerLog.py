import pickle
import logging
import logging.handlers
import socketserver
import struct
from TestBroadcastTree import CustomFilter, Test1, Test2, Test3
import sys
import threading
import time
import os
from queue import Queue

q = Queue(0)


def worker():
    while True:
        item = q.get()
        if item is None:
            break
        logger = logging.getLogger('my_logger')
        logger.handle(item)
        q.task_done()


class TestHandler(logging.StreamHandler):
    currentTest = Test1()
    currentTest.stop_everything()
    currentTest.set_initial_settings()
    currentTest.print_test()
    t = threading.Thread(target=currentTest.set_router_state)
    t.start()
    nextTests = [Test2(), Test3()]
    main = None

    def emit(self, record):
        super().emit(record)
        if TestHandler.currentTest and TestHandler.currentTest.test(record):
            if len(TestHandler.nextTests) > 0:
                TestHandler.t.join()
                TestHandler.currentTest = TestHandler.nextTests.pop(0)
                TestHandler.currentTest.print_test()
                TestHandler.t = threading.Thread(target=TestHandler.currentTest.set_router_state)
                TestHandler.t.start()
            else:
                TestHandler.currentTest = None
                TestHandler.main.abort = True


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            q.put(item=record, block=False)

    def unPickle(self, data):
        return pickle.loads(data)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        TestHandler.main = self
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = False
        self.timeout = 0.0001
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = False
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def main():
    handler = TestHandler(sys.stdout)
    formatter = logging.Formatter('%(name)-50s %(levelname)-8s %(asctime)-20s %(tree)-35s %(vif)-2s %(interfacename)-5s %(routername)-2s %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger('my_logger').addHandler(handler)
    logging.getLogger('my_logger').addFilter(CustomFilter())

    t1 = threading.Thread(target=worker, daemon=True)
    t2 = threading.Thread(target=worker, daemon=True)
    t3 = threading.Thread(target=worker, daemon=True)
    t1.start()
    t2.start()
    t3.start()
    tcpserver = LogRecordSocketReceiver(host='172.16.1.100')
    print('About to start TCP server...')

    t11 = threading.Thread(target=tcpserver.serve_until_stopped)
    t21 = threading.Thread(target=tcpserver.serve_until_stopped)
    t11.start()
    t21.start()

    t11.join()
    t21.join()

    time.sleep(10)
    os.system('kill -9 %d' % os.getpid())


if __name__ == '__main__':
    main()
