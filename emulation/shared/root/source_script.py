import socket
import sys
import fileinput
import os
import logging.handlers
import logging
import subprocess


#INICIALIZACAO
CLIENT_NAME = ""
CLIENT_IP = ""
SERVER_IP = ""

logger = logging.getLogger('tests')
logger.setLevel(logging.DEBUG)

CLIENT_PORT=12000

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('',12000))
process = None

#setlogger()



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
		record.tree = ''
		record.vif = ''
		record.interfacename = ''
		return True


def setLogger():
	global logger
	print("in setting logger")
	#logger.addHandler(logging.StreamHandler(sys.stdout))
	socketHandler = logging.handlers.SocketHandler(SERVER_IP, logging.handlers.DEFAULT_TCP_LOGGING_PORT)
	socketHandler.addFilter(RootFilter(CLIENT_NAME))
	logger.addHandler(socketHandler)


def sendTo_logger(message):
	global logger
	print("Message to server: " + message)
	logger.debug(message)


def settings(client_name, server_ip):
	global CLIENT_NAME
	CLIENT_NAME = client_name

	global SERVER_IP
	SERVER_IP = server_ip

	setLogger()


def start_process():
	global process
	command = "python3 server.py -i eth0 -a"
	sendTo_logger(command)
	process = subprocess.Popen(command.split())


def stop_process():
	global process
	command = "kill python3 server.py"
	sendTo_logger(command)
	process.kill()


while True:
	try:
		(msg,addr) = sock.recvfrom(1024)
		msg = msg.decode('utf-8')
		cmds = msg.split()
		if cmds[0] == "set" and len(cmds) == 3:
			settings(cmds[1], cmds[2])
		elif cmds[0] == "start":
			start_process()
		elif cmds[0] == "stop":
			stop_process()
	except:
		pass
sock.close()
