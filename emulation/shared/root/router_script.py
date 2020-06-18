import socket
import time         
import sys
import fileinput
import os
import logging.handlers
import logging
import ram_cpu


#INICIALIZACAO
CLIENT_NAME = ""
SERVER_IP = ""

logger = logging.getLogger('tests')
logger.setLevel(logging.DEBUG)

CLIENT_PORT=12000

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('',12000))

MONITOR_PROCESS = None

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


def stop_process():
	command = "python3 Run.py -stop"
	sendTo_logger(command)
	os.system(command)
	ram_cpu.stop_monitoring()

	
def start_process():
	command = "python3 Run.py -start"
	sendTo_logger(command)
	os.system(command)

	hpim_pid = int(open("/tmp/Daemon-pim.pid", "r").readline()[:-1])
	ram_cpu.start_monitoring(hpim_pid)


def restart_process():
	stop_process()
	start_process()


def add_interface(interface):
	command = "python3 Run.py -ai " + interface
	sendTo_logger(command)
	os.system(command)


def add_igmp_interface(interface):
	command = "python3 Run.py -aiigmp " + interface
	sendTo_logger(command)
	os.system(command)


def change_cost(interface, cost):
	command = "vtysh -c \"configure terminal\" -c \"interface {}\" -c \"ip ospf cost {}\"".format(interface, cost)
	sendTo_logger(command)
	os.system(command)


def remove_interface(interface):
	command = "python3 Run.py -ri " + interface
	sendTo_logger(command)
	os.system(command)


def remove_igmp_interface(interface):
	command = "python3 Run.py -riigmp " + interface
	sendTo_logger(command)
	os.system(command)


def shutdown_interface(interface):
	command = "ifconfig " + interface + " down"
	sendTo_logger(command)
	os.system(command)
	remove_interface(interface)
	remove_igmp_interface(interface)


def enable_interface(interface):
	command = "ifconfig " + interface + " up"
	sendTo_logger(command)
	os.system(command)


def tester():
	command = "python3 Run.py -t " + CLIENT_NAME + " " + SERVER_IP
	sendTo_logger(command)
	os.system(command)


def verbose():
	command = "python3 Run.py -v"
	sendTo_logger(command)
	os.system(command)


while True:
	(msg,addr) = sock.recvfrom(1024)
	msg = msg.decode('utf-8')
	cmds = msg.split()
	if cmds[0] == "set" and len(cmds) == 3:
		settings(cmds[1], cmds[2])
	elif cmds[0] == "start":
		start_process()
	elif cmds[0] == "stop":
		stop_process()
	elif cmds[0] == "restart":
		restart_process()
	elif cmds[0] == "t":
		tester()
	elif cmds[0] == "ai" and len(cmds) == 2:
		add_interface(cmds[1])
	elif cmds[0] == "ri" and len(cmds) == 2:
		remove_interface(cmds[1])
	elif cmds[0] == "aiigmp" and len(cmds) == 2:
		add_igmp_interface(cmds[1])
	elif cmds[0] == "riigmp" and len(cmds) == 2:
		remove_igmp_interface(cmds[1])
	elif cmds[0] == "shutdown-interface" and len(cmds) == 2:
		shutdown_interface(cmds[1])
	elif cmds[0] == "enable-interface" and len(cmds) == 2:
		enable_interface(cmds[1])
	elif cmds[0] == "cost" and len(cmds) == 3:
		change_cost(cmds[1], cmds[2])
	elif cmds[0] == "v":
		verbose()

sock.close()
