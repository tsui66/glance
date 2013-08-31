#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import sys
import socket

# Somes libs depends of OS
is_BSD = sys.platform.find('bsd') != -1
is_Linux = sys.platform.startswith('linux')
is_Mac = sys.platform.startswith('darwin')
is_Windows = sys.platform.startswith('win')

try:
    # psutil is the main library used to grab stats
    import psutil
except ImportError:
    print('PsUtil module not found. Glances cannot start.')
    sys.exit(1)

psutil_version = tuple([int(num) for num in psutil.__version__.split('.')])
# this is not a mistake: psutil 0.5.1 is detected as 0.5.0
if psutil_version < (0, 5, 0):
    print('PsUtil version %s detected.' % psutil.__version__)
    print('PsUtil 0.5.1 or higher is needed. Glances cannot start.')
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

if is_Linux:
    try:
        import sensors
    except ImportError:
        sensors_lib_tag = False
    else:
        sensors_lib_tag = True
else:
    sensors_lib_tag = False

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
class glanceGrabHDDTemp:
    """
    Get hddtemp stats using a socket connection
    """
    cache = ""
    address = "127.0.0.1"
    port = 7634

    def __init__(self):
        """
        Init hddtemp stats
        """
        try:
            sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sck.connect((self.address, self.port))
            sck.close()
        except:
            self.initok = False
        else:
            self.initok = True

    def __update__(self):
        """
        Update the stats
        """
        # Reset the list
        self.hddtemp_list = []

        if self.initok:
            data = ""
            # Taking care of sudden deaths/stops of hddtemp daemon
            try:
                sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sck.connect((self.address, self.port))
                data = sck.recv(4096)
                sck.close()
            except:
                hddtemp_current = {}
                hddtemp_current['label'] = "hddtemp is gone"
                hddtemp_current['value'] = 0
                self.hddtemp_list.append(hddtemp_current)
                return
            else:
                # Considering the size of "|/dev/sda||0||" as the minimum
                if len(data) < 14:
                    if len(self.cache) == 0:
                        data = "|hddtemp error||0||"
                    else:
                        data = self.cache
                self.cache = data
                fields = data.decode('utf-8').split("|")
                devices = (len(fields) - 1) // 5
                for i in range(0, devices):
                    offset = i * 5
                    hddtemp_current = {}
                    temperature = fields[offset + 3]
                    if temperature == "ERR":
                        hddtemp_current['label'] = "hddtemp error"
                        hddtemp_current['value'] = 0
                    elif temperature == "SLP":
                        hddtemp_current['label'] = fields[offset + 1].split("/")[-1] + " is sleeping"
                        hddtemp_current['value'] = 0
                    elif temperature == "UNK":
                        hddtemp_current['label'] = fields[offset + 1].split("/")[-1] + " is unknown"
                        hddtemp_current['value'] = 0
                    else:
                        hddtemp_current['label'] = fields[offset + 1].split("/")[-1]
                        try:
                            hddtemp_current['value'] = int(temperature)
                        except TypeError:
                            hddtemp_current['label'] = fields[offset + 1].split("/")[-1] + " is unknown"
                            hddtemp_current['value'] = 0
                    self.hddtemp_list.append(hddtemp_current)

    def get(self):
        self.__update__()
        return self.hddtemp_list
