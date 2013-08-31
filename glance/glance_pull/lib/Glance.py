#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


__version__ = "1.1"
__author__ = "mepoo"


import os
import sys
import time
import calendar
from datetime import datetime
import platform

is_BSD = sys.platform.find('bsd') != -1
is_Linux = sys.platform.startswith('linux')
is_Mac = sys.platform.startswith('darwin')
is_Windows = sys.platform.startswith('win')

try:
    import psutil
except ImportError:
    print 'psutil module not found. Please install psutil module.'
    sys.exit(1)

psutil_version = tuple([int(num) for num in psutil.__version__.split('.')])
if psutil_version < (0, 5, 0):
    print 'psutil version %s detected' % psutil_version
    print 'psutil 0.5.1 higher is needed.'
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

if is_Linux:
    try:
        import batinfo
    except ImportError:
        batinfo_lib_tag = False
    else:
        batinfo_lib_tag = True
else:
    batinfo_lib_tag = False

if not is_Mac:
    psutil_get_io_counter_tag = True
else:
    #get_io_counters() not available on OS X
    psutil_get_io_counter_tag = False

from oslo.config import cfg

from GlanceFileSystem import glancesGrabFs
from GlanceProcesses import GlancesGrabProcesses
from GlanceHDDTemp import glanceGrabHDDTemp
from GlanceBattery import glanceGrabBat
from GlanceSensors import glanceGrabSensors
from GlanceList import monitorList 


glance_opts = [
        cfg.StrOpt('',
                    default = '',
                    help = '')
]

CONF = cfg.CONF
CONF.register_opts(glance_opts)


#Default tag
sensors_tag = False
hddtemp_tag = False
network_tag = True
fs_tag = True
diskio_tag = True
process_tag = True

last_update_times = {}

class GlanceStats:
    """
    This class store, update and give stats
    """

    def __init__(self):
        """
        Init the stats
        """

        self._init_host()

        # Init the grab error tags
        # for managing error during stats grab
        # By default, we *hope* that there is no error
        self.network_error_tag = False
        self.diskio_error_tag = False

        # Init the fs stats
        try:
            self.glancesgrabfs = glancesGrabFs()
        except Exception:
            self.glancesgrabfs = {}

        # Init the sensors stats (optional)
        if sensors_tag:
            try:
                self.glancesgrabsensors = glanceGrabSensors()
            except Exception:
                self.sensors_tag = False

        # Init the hddtemp stats (optional)
        if hddtemp_tag:
            try:
                self.glancesgrabhddtemp = glanceGrabHDDTemp()
            except Exception:
                self.hddtemp_tag = False
        if batinfo_lib_tag:
            self.glancesgrabbat = glanceGrabBat()

        self.process_list_refresh = True
        self.process_list_sortedby = ''
        self.glancesgrabprocesses = GlancesGrabProcesses()

    def _init_host(self):
        self.host = {}
        self.host['os_name'] = platform.system()
        self.host['hostname'] = platform.node()
        # More precise but not user friendly
        #~ if platform.uname()[4]:
            #~ self.host['platform'] = platform.uname()[4]
        #~ else:
            #~ self.host['platform'] = platform.architecture()[0]
        # This one is better
        self.host['platform'] = platform.architecture()[0]
        is_archlinux = os.path.exists(os.path.join("/", "etc", "arch-release"))
        if self.host['os_name'] == "Linux":
            if is_archlinux:
                self.host['linux_distro'] = "Arch Linux"
            else:
                linux_distro = platform.linux_distribution()
                self.host['linux_distro'] = " ".join(linux_distro[:2])
            self.host['os_version'] = platform.release()
        elif self.host['os_name'] == "FreeBSD":
            self.host['os_version'] = platform.release()
        elif self.host['os_name'] == "Darwin":
            self.host['os_version'] = platform.mac_ver()[0]
        elif self.host['os_name'] == "Windows":
            os_version = platform.win32_ver()
            self.host['os_version'] = " ".join(os_version[::2])
        else:
            self.host['os_version'] = ""

    def __update__(self, input_stats):
        """
        Update the stats
        """
        # CPU
        cputime = psutil.cpu_times(percpu=False)
        cputime_total = cputime.user + cputime.system + cputime.idle
        # Only available on some OS
        if hasattr(cputime, 'nice'):
            cputime_total += cputime.nice
        if hasattr(cputime, 'iowait'):
            cputime_total += cputime.iowait
        if hasattr(cputime, 'irq'):
            cputime_total += cputime.irq
        if hasattr(cputime, 'softirq'):
            cputime_total += cputime.softirq
        if not hasattr(self, 'cputime_old'):
            self.cputime_old = cputime
            self.cputime_total_old = cputime_total
            self.cpu = {}
        else:
            self.cputime_new = cputime
            self.cputime_total_new = cputime_total
            try:
                percent = 100 / (self.cputime_total_new -
                                 self.cputime_total_old)
                self.cpu = {'user': (self.cputime_new.user -
                                     self.cputime_old.user) * percent,
                            'system': (self.cputime_new.system -
                                       self.cputime_old.system) * percent,
                            'idle': (self.cputime_new.idle -
                                     self.cputime_old.idle) * percent}
                if hasattr(self.cputime_new, 'nice'):
                    self.cpu['nice'] = (self.cputime_new.nice -
                                        self.cputime_old.nice) * percent
                if hasattr(self.cputime_new, 'iowait'):
                    self.cpu['iowait'] = (self.cputime_new.iowait -
                                          self.cputime_old.iowait) * percent
                if hasattr(self.cputime_new, 'irq'):
                    self.cpu['irq'] = (self.cputime_new.irq -
                                       self.cputime_old.irq) * percent
                self.cputime_old = self.cputime_new
                self.cputime_total_old = self.cputime_total_new
            except Exception:
                self.cpu = {}

        # Per-CPU
        percputime = psutil.cpu_times(percpu=True)
        percputime_total = []
        for i in range(len(percputime)):
            percputime_total.append(percputime[i].user +
                                    percputime[i].system +
                                    percputime[i].idle)
        # Only available on some OS
        for i in range(len(percputime)):
            if hasattr(percputime[i], 'nice'):
                percputime_total[i] += percputime[i].nice
        for i in range(len(percputime)):
            if hasattr(percputime[i], 'iowait'):
                percputime_total[i] += percputime[i].iowait
        for i in range(len(percputime)):
            if hasattr(percputime[i], 'irq'):
                percputime_total[i] += percputime[i].irq
        for i in range(len(percputime)):
            if hasattr(percputime[i], 'softirq'):
                percputime_total[i] += percputime[i].softirq
        if not hasattr(self, 'percputime_old'):
            self.percputime_old = percputime
            self.percputime_total_old = percputime_total
            self.percpu = []
        else:
            self.percputime_new = percputime
            self.percputime_total_new = percputime_total
            perpercent = []
            self.percpu = []
            try:
                for i in range(len(self.percputime_new)):
                    perpercent.append(100 / (self.percputime_total_new[i] -
                                             self.percputime_total_old[i]))
                    cpu = {'user': (self.percputime_new[i].user -
                                    self.percputime_old[i].user) * perpercent[i],
                           'system': (self.percputime_new[i].system -
                                      self.percputime_old[i].system) * perpercent[i],
                           'idle': (self.percputime_new[i].idle -
                                    self.percputime_old[i].idle) * perpercent[i]}
                    if hasattr(self.percputime_new[i], 'nice'):
                        cpu['nice'] = (self.percputime_new[i].nice -
                                       self.percputime_old[i].nice) * perpercent[i]
                    if hasattr(self.percputime_new[i], 'iowait'):
                        cpu['iowait'] = (self.percputime_new[i].iowait -
                                         self.percputime_old[i].iowait) * perpercent[i]
                    if hasattr(self.percputime_new[i], 'irq'):
                        cpu['irq'] = (self.percputime_new[i].irq -
                                      self.percputime_old[i].irq) * perpercent[i]
                    if hasattr(self.percputime_new[i], 'softirq'):
                        cpu['softirq'] = (self.percputime_new[i].softirq -
                                          self.percputime_old[i].softirq) * perpercent[i]
                    self.percpu.append(cpu)
                self.percputime_old = self.percputime_new
                self.percputime_total_old = self.percputime_total_new
            except Exception:
                self.percpu = []

        # LOAD
        if hasattr(os, 'getloadavg'):
            getload = os.getloadavg()
            self.load = {'min1': getload[0],
                         'min5': getload[1],
                         'min15': getload[2]}
        else:
            self.load = {}

        # MEM
        # psutil >= 0.6
        if psutil_mem_vm:
            # RAM
            phymem = psutil.virtual_memory()

            # buffers and cached (Linux, BSD)
            buffers = getattr(phymem, 'buffers', 0)
            cached = getattr(phymem, 'cached', 0)

            # active and inactive not available on Windows
            active = getattr(phymem, 'active', 0)
            inactive = getattr(phymem, 'inactive', 0)

            # phymem free and usage
            total = phymem.total
            free = phymem.available  # phymem.free + buffers + cached
            used = total - free

            self.mem = {'total': total,
                        'percent': phymem.percent,
                        'used': used,
                        'free': free,
                        'active': active,
                        'inactive': inactive,
                        'buffers': buffers,
                        'cached': cached}

            # Swap
            # try... is an hack for issue #152
            try:
                virtmem = psutil.swap_memory()
            except Exception:
                self.memswap = {}
            else:
                self.memswap = {'total': virtmem.total,
                                'used': virtmem.used,
                                'free': virtmem.free,
                                'percent': virtmem.percent}
        else:
            # psutil < 0.6
            # RAM
            if hasattr(psutil, 'phymem_usage'):
                phymem = psutil.phymem_usage()

                # buffers and cached (Linux, BSD)
                buffers = getattr(psutil, 'phymem_buffers', 0)()
                cached = getattr(psutil, 'cached_phymem', 0)()

                # phymem free and usage
                total = phymem.total
                free = phymem.free + buffers + cached
                used = total - free

                # active and inactive not available for psutil < 0.6
                self.mem = {'total': total,
                            'percent': phymem.percent,
                            'used': used,
                            'free': free,
                            'buffers': buffers,
                            'cached': cached}
            else:
                self.mem = {}

            # Swap
            if hasattr(psutil, 'virtmem_usage'):
                virtmem = psutil.virtmem_usage()
                self.memswap = {'total': virtmem.total,
                                'used': virtmem.used,
                                'free': virtmem.free,
                                'percent': virtmem.percent}
            else:
                self.memswap = {}

        # NET
        if network_tag and not self.network_error_tag:
            self.network = []

            # By storing time data we enable Rx/s and Tx/s calculations in the
            # XML/RPC API, which would otherwise be overly difficult work
            # for users of the API
            time_since_update = getTimeSinceLastUpdate('net')

            if psutil_net_io_counters:
                # psutil >= 1.0.0
                get_net_io_counters = psutil.net_io_counters(pernic=True)
            else:
                # psutil < 1.0.0
                get_net_io_counters = psutil.network_io_counters(pernic=True)

            if not hasattr(self, 'network_old'):
                try:
                    self.network_old = get_net_io_counters
                except IOError:
                    self.network_error_tag = True
            else:
                self.network_new = get_net_io_counters
                for net in self.network_new:
                    try:
                        # Try necessary to manage dynamic network interface
                        netstat = {}
                        netstat['time_since_update'] = time_since_update
                        netstat['interface_name'] = net
                        netstat['cumulative_rx'] = self.network_new[net].bytes_recv
                        netstat['rx'] = (self.network_new[net].bytes_recv -
                                         self.network_old[net].bytes_recv)
                        netstat['cumulative_tx'] = self.network_new[net].bytes_sent
                        netstat['tx'] = (self.network_new[net].bytes_sent -
                                         self.network_old[net].bytes_sent)
                        netstat['cumulative_cx'] = (netstat['cumulative_rx'] +
                                                    netstat['cumulative_tx'])
                        netstat['cx'] = netstat['rx'] + netstat['tx']
                    except Exception:
                        continue
                    else:
                        self.network.append(netstat)
                self.network_old = self.network_new

        # SENSORS
        if sensors_tag:
            self.sensors = self.glancesgrabsensors.get()

        # HDDTEMP
        if hddtemp_tag:
            self.hddtemp = self.glancesgrabhddtemp.get()

        # BATERRIES INFORMATION
        if batinfo_lib_tag:
            self.batpercent = self.glancesgrabbat.getcapacitypercent()

        # DISK I/O
        if diskio_tag and not self.diskio_error_tag:
            time_since_update = getTimeSinceLastUpdate('disk')
            self.diskio = []
            if not hasattr(self, 'diskio_old'):
                try:
                    self.diskio_old = psutil.disk_io_counters(perdisk=True)
                except IOError:
                    self.diskio_error_tag = True
            else:
                self.diskio_new = psutil.disk_io_counters(perdisk=True)
                for disk in self.diskio_new:
                    try:
                        # Try necessary to manage dynamic disk creation/del
                        diskstat = {}
                        diskstat['time_since_update'] = time_since_update
                        diskstat['disk_name'] = disk
                        diskstat['read_bytes'] = (
                            self.diskio_new[disk].read_bytes -
                            self.diskio_old[disk].read_bytes)
                        diskstat['write_bytes'] = (
                            self.diskio_new[disk].write_bytes -
                            self.diskio_old[disk].write_bytes)
                    except Exception:
                        continue
                    else:
                        self.diskio.append(diskstat)
                self.diskio_old = self.diskio_new

        # FILE SYSTEM
        if fs_tag:
            self.fs = self.glancesgrabfs.get()

        # PROCESS
        if process_tag:
            self.glancesgrabprocesses.update()
            processcount = self.glancesgrabprocesses.getcount()
            process = self.glancesgrabprocesses.getlist()
            if not hasattr(self, 'process'):
                self.processcount = {}
                self.process = []
            else:
                self.processcount = processcount
                self.process = process

        # Get the current date/time
        self.now = datetime.now()

        # Get the number of core (CPU) (Used to display load alerts)
        self.core_number = psutil.NUM_CPUS

    def update(self, input_stats={}):
        # Update the stats
        self.__update__(input_stats)

    def getSortedBy(self):
        return self.process_list_sortedby

    def getAll(self):
        return self.all_stats

    def getHost(self):
        return self.host

    def getServer(self):
        return self.host

    def getCpu(self):
        return self.cpu

    def getPerCpu(self):
        return self.percpu

    def getCore(self):
        return self.core_number

    def getLoad(self):
        return self.load

    def getMem(self):
        return self.mem

    def getMemSwap(self):
        return self.memswap

    def getNetwork(self):
        if network_tag:
            return sorted(self.network,
                          key=lambda network: network['interface_name'])
        else:
            return []

    def getSensors(self):
        if sensors_tag:
            return sorted(self.sensors,
                          key=lambda sensors: sensors['label'])
        else:
            return []

    def getHDDTemp(self):
        if hddtemp_tag:
            return sorted(self.hddtemp,
                          key=lambda hddtemp: hddtemp['label'])
        else:
            return []

    def getBatPercent(self):
        if batinfo_lib_tag:
            return self.batpercent
        else:
            return []

    def getDiskIO(self):
        if diskio_tag:
            return sorted(self.diskio, key=lambda diskio: diskio['disk_name'])
        else:
            return []

    def getFs(self):
        if fs_tag:
            return sorted(self.fs, key=lambda fs: fs['mnt_point'])
        else:
            return []

    def getProcessCount(self):
        if process_tag:
            return self.processcount
        else:
            return 0

    def getProcessList(self, sortedby='auto'):
        """
        Return the sorted process list
        """

        if not process_tag:
            return []
        if self.process == {} or 'limits' not in globals():
            return self.process

        sortedReverse = True
        if sortedby == 'auto':
            # Auto selection (default: sort by CPU%)
            sortedby = 'cpu_percent'
            # Dynamic choice
            #if ('iowait' in self.cpu and
            #    self.cpu['iowait'] > limits.getCPUWarning(stat='iowait')):
                # If CPU IOWait > 70% sort by IORATE usage
            #    sortedby = 'io_counters'
            #elif (self.mem['total'] != 0 and
            #      self.mem['used'] * 100 / self.mem['total'] > limits.getMEMWarning()):
                # If global MEM > 70% sort by MEM usage
            #    sortedby = 'memory_percent'
        elif sortedby == 'name':
            sortedReverse = False

        if sortedby == 'io_counters':
            try:
                # Sort process by IO rate (sum IO read + IO write)
                listsorted = sorted(self.process,
                                    key=lambda process: process[sortedby][0] -
                                    process[sortedby][2] + process[sortedby][1] -
                                    process[sortedby][3], reverse=sortedReverse)
            except:
                listsorted = sorted(self.process, key=lambda process: process['cpu_percent'],
                                    reverse=sortedReverse)
        else:
            # Others sorts
            listsorted = sorted(self.process, key=lambda process: process[sortedby],
                                reverse=sortedReverse)

        # Save the latest sort type in a global var
        self.process_list_sortedby = sortedby

        # Return the sorted list
        return listsorted

    def getNow(self):
        d = datetime.utcnow()
        _unix = calendar.timegm(d.utctimetuple())
        return _unix

    def getUptime(self):

        with open('/proc/uptime', 'r') as line:
            contents = line.read().split()

        total_seconds = float(contents[0])

        MINUTE  = 60
        HOUR    = MINUTE * 60
        DAY     = HOUR * 24

        days    = int( total_seconds / DAY )
        hours   = int( ( total_seconds % DAY ) / HOUR )
        minutes = int( ( total_seconds % HOUR ) / MINUTE )
        seconds = int( total_seconds % MINUTE )

        uptime = "{0} days {1} hours {2} minutes {3} seconds".format(days, hours, minutes, seconds)

        return uptime


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
