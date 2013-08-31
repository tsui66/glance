#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import sys

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

# sensors library (optional; Linux-only)
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
class glanceGrabSensors:
    """
    Get sensors stats using the PySensors library
    """

    def __init__(self):
        """
        Init sensors stats
        """

        try:
            sensors.init()
        except:
            self.initok = False
        else:
            self.initok = True

    def __update__(self):
        """
        Update the stats
        """

        # Reset the list
        self.sensors_list = []

        # grab only temperature stats
        if self.initok:
            for chip in sensors.iter_detected_chips():
                for feature in chip:
                    sensors_current = {}
                    if feature.name.startswith('temp'):
                        sensors_current['label'] = feature.label[:20]
                        sensors_current['value'] = int(feature.get_value())
                        self.sensors_list.append(sensors_current)

    def get(self):
        self.__update__()
        return self.sensors_list

    def quit(self):
        if self.initok:
            sensors.cleanup()
