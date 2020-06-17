import psutil, os
import time
import threading
from datetime import datetime
import json

RELATIONS_MONITOR = None
MEMORY_MONITOR = None
CPU_MONITOR = None
RELATIONS_MONITOR_THREAD = None
MEMORY_MONITOR_THREAD = None
CPU_MONITOR_THREAD = None
REFRESH_TIME = 0.5

'''

##############PROCESS BASIC INFO ################

pid = p.pid
print('PID: ' + str(pid))
name = p.name()
print('NAME: ' + name)
status = p.status()
print('STATUS: ' + status)

###################################################
'''

def get_python_proccesses():
    python_processes = []
    own_process = psutil.Process(os.getpid())
    for proc in psutil.process_iter():
        if proc.name() == "python3" and proc.pid != own_process.pid:
            python_processes.append(proc)
            print(proc)

    return python_processes



class MemoryMonitor:
    # rss is the Resident Set Size, which is the actual physical memory the process is using
    # vms is the Virtual Memory Size which is the virtual memory that process is using

    def __init__(self, _process, filename):
        self.keep_measuring = True
        self.process = _process
        self.filename = filename

    def measure_usage(self):
        f = open("memory_monitor_" + self.filename, "w")
        while self.keep_measuring:
            t = datetime.now().strftime("%H:%M:%S.%f")
            try:
                current_rss = self.process.memory_info().rss  # in bytes
                current_percent = self.process.memory_percent()
                j = {"CURRENT_RSS": current_rss, "CURRENT_PRECENT": current_percent}
                f.write(t + "->" + json.dumps(j) + "\n")
            except psutil.NoSuchProcess:
                print("process no longer exists!")
                self.keep_measuring = False
            except psutil.AccessDenied:
                print("permission denied.. continuing")
            except:
                pass

            time.sleep(REFRESH_TIME)
        f.close()


class CPUMonitor:
    def __init__(self, _process, filename):
        self.keep_measuring = True
        self.process = _process
        self.filename = filename

    def measure_usage(self):
        f = open("cpu_monitor_" + self.filename, "w")
        while self.keep_measuring:
            t = datetime.now().strftime("%H:%M:%S.%f")
            try:
                current_cpu_times = self.process.cpu_times()  # in bytes
                current_cpu_percent = self.process.cpu_percent()

                j = {"CURRENT_CPU_TIMES": current_cpu_times, "CURRENT_PRECENT": current_cpu_percent}
                f.write(t + "->" + json.dumps(j) + "\n")
            except psutil.NoSuchProcess:
                print("process no longer exists!")
                self.keep_measuring = False
            except psutil.AccessDenied:
                print("permission denied.. continuing")
            except:
                pass

            time.sleep(REFRESH_TIME)
        f.close()


class RelationsMonitor:
    def __init__(self, _process, filename):
        self.keep_measuring = True
        self.process = _process
        self.filename = filename

    def measure_usage(self):
        f = open("relations_monitor_" + self.filename, "w")
        while self.keep_measuring:
            t = datetime.now().strftime("%H:%M:%S.%f")
            try:
                current_children = self.process.children(recursive=True)
                current_threads = self.process.threads()
                current_num_threads = self.process.num_threads()
                current_connections = self.process.connections()
                current_io_counters = self.process.io_counters()

                j = {"CHILDREN": current_children, "THREADS": current_threads, "NUM_THREADS": current_num_threads,
                     "CONNECTIONS": current_connections, "IO_COUNTER": current_io_counters}
                f.write(t + "->" + json.dumps(j) + "\n")
            except psutil.NoSuchProcess:
                print("process no longer exists!")
                self.keep_measuring = False
            except psutil.AccessDenied:
                print("permission denied.. continuing")
            except:
                pass

            time.sleep(REFRESH_TIME)
        f.close()


def start_monitoring(pid):
    global MEMORY_MONITOR
    global CPU_MONITOR
    global RELATIONS_MONITOR
    global MEMORY_MONITOR_THREAD
    global CPU_MONITOR_THREAD
    global RELATIONS_MONITOR_THREAD

    p = psutil.Process(pid)
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    filename = current_time + ".txt"

    MEMORY_MONITOR = MemoryMonitor(p, filename)
    CPU_MONITOR = CPUMonitor(p, filename)
    RELATIONS_MONITOR = RelationsMonitor(p, filename)

    MEMORY_MONITOR_THREAD = threading.Thread(target=MEMORY_MONITOR.measure_usage)
    MEMORY_MONITOR_THREAD.start()

    CPU_MONITOR_THREAD = threading.Thread(target=CPU_MONITOR.measure_usage)
    CPU_MONITOR_THREAD.start()

    RELATIONS_MONITOR_THREAD = threading.Thread(target=RELATIONS_MONITOR.measure_usage)
    RELATIONS_MONITOR_THREAD.start()


def stop_monitoring():
    global MEMORY_MONITOR
    global CPU_MONITOR
    global RELATIONS_MONITOR
    global MEMORY_MONITOR_THREAD
    global CPU_MONITOR_THREAD
    global RELATIONS_MONITOR_THREAD
    if MEMORY_MONITOR is not None:
        MEMORY_MONITOR.keep_measuring = False
        MEMORY_MONITOR_THREAD.join()
    if CPU_MONITOR is not None:
        CPU_MONITOR.keep_measuring = False
        CPU_MONITOR_THREAD.join()
    if RELATIONS_MONITOR is not None:
        RELATIONS_MONITOR.keep_measuring = False
        RELATIONS_MONITOR_THREAD.join()
