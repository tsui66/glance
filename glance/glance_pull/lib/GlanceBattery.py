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

# batinfo library (optional; Linux-only)
if is_Linux:
    try:
        import batinfo
    except ImportError:
        batinfo_lib_tag = False
    else:
        batinfo_lib_tag = True
else:
    batinfo_lib_tag = False

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

class glanceGrabBat:
    """
    Get batteries stats using the Batinfo librairie
    """

    def __init__(self):
        """
        Init batteries stats
        """
        if batinfo_lib_tag:
            try:
                self.bat = batinfo.batteries()
                self.bat.stat[0]["capacity"]
                self.initok = True
                self.__update__()
            except:
                self.initok = False
        else:
            self.initok = False

    def __update__(self):
        """
        Update the stats
        """

        if self.initok:
            try:
                self.bat.update()
            except:
                self.bat_list = []
            else:
                self.bat_list = self.bat.stat
        else:
            self.bat_list = []

    def get(self):
        # Update the stats
        self.__update__()
        return self.bat_list

    def getcapacitypercent(self):
        if not self.initok or self.bat_list == []:
            return []
        # Init the bsum (sum of percent) and bcpt (number of batteries)
        # and Loop over batteries (yes a computer could have more than 1 battery)
        bsum = 0
        for bcpt in range(len(self.get())):
            bsum = bsum + int(self.bat_list[bcpt].capacity)
        bcpt = bcpt + 1
        # Return the global percent
        return int(bsum / bcpt)
