#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import sys
import time
from  datetime import datetime, timedelta
from glance import log as logging

LOG = logging.getLogger(__name__)

# Somes libs depends of OS
is_BSD = sys.platform.find('bsd') != -1
is_Linux = sys.platform.startswith('linux')
is_Mac = sys.platform.startswith('darwin')
is_Windows = sys.platform.startswith('win')

try:
    # psutil is the main library used to grab stats
    import psutil
except ImportError:
    LOG.warning('PsUtil module not found. Glances cannot start.')
    sys.exit(1)

psutil_version = tuple([int(num) for num in psutil.__version__.split('.')])
# this is not a mistake: psutil 0.5.1 is detected as 0.5.0
if psutil_version < (0, 5, 0):
    LOG.warning('PsUtil version %s detected.' % psutil.__version__)
    LOG.warning('PsUtil 0.5.1 or higher is needed. Glances cannot start.')
    sys.exit(1)

try:
    # psutil.virtual_memory() only available from psutil >= 0.6
    psutil.virtual_memory()
except Exception:
    psutil_mem_vm = False
else:
    psutil_mem_vm = True

try:
    # psutil.net_io_counters() only available from psutil >= 1.0.0
    psutil.net_io_counters()
except Exception:
    psutil_net_io_counters = False
else:
    psutil_net_io_counters = True

if not is_Mac:
    psutil_get_io_counter_tag = True
else:
    # get_io_counters() not available on OS X
    psutil_get_io_counter_tag = False


from oslo.config import cfg

glance_opts = [
        cfg.StrOpt('',
                    default = '',
                    help = '')
]

CONF = cfg.CONF
CONF.register_opts(glance_opts)

# Default tag
sensors_tag = False
hddtemp_tag = False
network_tag = True
diskio_tag = True
fs_tag = True
process_tag = True

# Global moved outside main for unit tests
last_update_times = {}
class GlancesGrabProcesses:
    """
    Get processed stats using the PsUtil lib
    """

    def __init__(self):
        """
        Init the io dict
        key = pid
        value = [ read_bytes_old, write_bytes_old ]
        """
        self.io_old = {}

    def __get_process_stats(self, proc):
        """
        Get process statistics
        """
        procstat = {}

        procstat['name'] = proc.name
        procstat['pid'] = proc.pid
        try:
            procstat['username'] = proc.username
        except KeyError:
            LOG.warning("Key error.")
            procstat['username'] = proc.uids.real
        procstat['cmdline'] = " ".join(proc.cmdline)
        procstat['memory_info'] = proc.get_memory_info()
        procstat['memory_percent'] = proc.get_memory_percent()
        procstat['status'] = str(proc.status)[:1].upper()
        procstat['cpu_times'] = proc.get_cpu_times()
        procstat['cpu_percent'] = proc.get_cpu_percent(interval=0)
        procstat['nice'] = proc.get_nice()

        # procstat['io_counters'] is a list:
        # [read_bytes, write_bytes, read_bytes_old, write_bytes_old, io_tag]
        # If io_tag = 0 > Access denied (display "?")
        # If io_tag = 1 > No access denied (display the IO rate)
        if psutil_get_io_counter_tag:
            try:
                # Get the process IO counters
                proc_io = proc.get_io_counters()
                io_new = [proc_io.read_bytes, proc_io.write_bytes]
            except psutil.AccessDenied:
                LOG.exception("Access denied to process IO (no root account)")
                # Put 0 in all values (for sort) and io_tag = 0 (for display)
                procstat['io_counters'] = [0, 0] + [0, 0]
                io_tag = 0
            else:
                # For IO rate computation
                # Append saved IO r/w bytes
                try:
                    procstat['io_counters'] = io_new + self.io_old[procstat['pid']]
                except KeyError:
                    LOG.warning("Key error.")
                    procstat['io_counters'] = io_new + [0, 0]
                # then save the IO r/w bytes
                self.io_old[procstat['pid']] = io_new
                io_tag = 1

            # Append the IO tag (for display)
            procstat['io_counters'] += [io_tag]

        return procstat

    def update(self):
        self.processlist = []
        self.processcount = {'total': 0, 'running': 0, 'sleeping': 0}

        time_since_update = getTimeSinceLastUpdate('process_disk')
        # For each existing process...
        for proc in psutil.process_iter():
            try:
                procstat = self.__get_process_stats(proc)
                procstat['time_since_update'] = time_since_update
                # ignore the 'idle' process on Windows and *BSD
                # ignore the 'kernel_task' process on OS X
                # waiting for upstream patch from psutil
                if (is_BSD and procstat['name'] == 'idle' or
                    is_Windows and procstat['name'] == 'System Idle Process' or
                    is_Mac and procstat['name'] == 'kernel_task'):
                    continue
                # Update processcount (global stattistics)
                try:
                    self.processcount[str(proc.status)] += 1
                except KeyError:
                    LOG.exception("Key did not exist, create it")
                    self.processcount[str(proc.status)] = 1
                else:
                    self.processcount['total'] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            else:
                # Update processlist
                self.processlist.append(procstat)

    def getcount(self):
        return self.processcount

    def getlist(self):
        return self.processlist

def getTimeSinceLastUpdate(IOType):
    global last_update_times
    assert(IOType in ['net', 'disk', 'process_disk'])
    current_time = time.time()
    last_time = last_update_times.get(IOType)
    if not last_time:
        time_since_update = 1
    else:
        time_since_update = current_time - last_time
        last_update_times[IOType] = current_time
    return time_since_update
