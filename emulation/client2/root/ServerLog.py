import pickle
import logging
import logging.handlers
import socketserver
import struct
from TestAssert import Test1, Test2
import sys
from threading import Lock

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    currentTest = Test1()
    nextTests = [Test2()]
    lock = Lock()
    main = None

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        logging.FileHandler('server.log').setLevel(logging.DEBUG)
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
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        logger.addFilter(logging.Filter('pim'))
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        #if record.routername == "R2":
        logger.handle(record)
        with LogRecordStreamHandler.lock:
            if LogRecordStreamHandler.currentTest and record.routername in ["R2","R3","R4","R5","R6"] and record.name in ("pim.KernelEntry.DownstreamInterface.Assert", "pim.KernelEntry.UpstreamInterface.Assert") and LogRecordStreamHandler.currentTest.test(record):
                if len(LogRecordStreamHandler.nextTests) > 0:
                    LogRecordStreamHandler.currentTest = LogRecordStreamHandler.nextTests.pop(0)
                if LogRecordStreamHandler.currentTest is None:
                    LogRecordStreamHandler.main.abort = 1




class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='10.5.5.100',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        handler.main = self
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
    logging.basicConfig(
        format='%(relativeCreated)5d %(name)-50s %(levelname)-8s %(tree)-35s %(vif)-2s %(routername)-2s %(message)s',
        )
        #filename='example.log')
    tcpserver = LogRecordSocketReceiver()
    print('About to start TCP server...')
    tcpserver.serve_until_stopped()

if __name__ == '__main__':
    main()