import pickle
import logging
import logging.handlers
import socketserver
import struct
from TestBroadcastTree import CustomFilter, Test1, Test2, Test3
import sys
import threading
from queue import Queue

q = Queue()


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
    currentTest.print_test()
    nextTests = [Test2(), Test3()]
    main = None

    def emit(self, record):
        super().emit(record)
        if TestHandler.currentTest and TestHandler.currentTest.test(record):
            if len(TestHandler.nextTests) > 0:
                TestHandler.currentTest = TestHandler.nextTests.pop(0)
                TestHandler.currentTest.print_test()
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
            q.put(item=record)

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
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def main():
    handler = TestHandler(sys.stdout)
    formatter = logging.Formatter('%(name)-50s %(levelname)-8s %(tree)-35s %(vif)-2s %(interfacename)-5s %(routername)-2s %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger('my_logger').addHandler(handler)
    logging.getLogger('my_logger').addFilter(CustomFilter())

    t = threading.Thread(target=worker)
    t.start()

    tcpserver = LogRecordSocketReceiver(host='10.5.5.7')
    print('About to start TCP server...')
    tcpserver.serve_until_stopped()


if __name__ == '__main__':
    main()
