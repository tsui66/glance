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
class monitorList:
    """
    This class describes the optionnal monitored processes list
    A list of 'important' processes to monitor.

    The list (Python list) is composed of items (Python dict)
    An item is defined (Dict keys'):
    * description: Description of the processes (max 16 chars)
    * regex: regular expression of the processes to monitor
    * command: (optionnal) shell command for extended stat
    * countmin: (optional) minimal number of processes
    * countmax: (optional) maximum number of processes
    """

    # Maximum number of items in the list
    __monitor_list_max_size = 10
    # The list
    __monitor_list = []

    def __init__(self):
        if config.has_section('monitor'):
            # Process monitoring list
            self.__setMonitorList('monitor', 'list')

    def __setMonitorList(self, section, key):
        """
        Init the monitored processes list
        The list is defined in the Glances configuration file
        """

        for l in range(1, self.__monitor_list_max_size + 1):
            value = {}
            key = "list_" + str(l) +"_"
            try:
                description = config.get_raw_option(section, key + "description")
                regex = config.get_raw_option(section, key + "regex")
                command = config.get_raw_option(section, key + "command")
                countmin = config.get_raw_option(section, key + "countmin")
                countmax = config.get_raw_option(section, key + "countmax")
            except:
                pass
            else:
                if (description != None and regex != None):
                    # Build the new item
                    value["description"] = description
                    value["regex"] = regex
                    value["command"] = command
                    value["countmin"] = countmin
                    value["countmax"] = countmax
                    # Add the item to the list
                    self.__monitor_list.append(value)

    def __str__(self):
        return str(self.__monitor_list)

    def __repr__(self):
        return self.__monitor_list

    def __getitem__(self, item):
        return self.__monitor_list[item]

    def __len__(self):
        return len(self.__monitor_list)

    def __get__(self, item, key):
        """
        Meta function to return key value of item
        None if not defined or item > len(list)
        """
        if (item < len(self.__monitor_list)):
            try:
                return self.__monitor_list[item][key]
            except:
                return None
        else:
            return None

    def getAll(self):
        return self.__monitor_list

    def setAll(self, newlist):
        self.__monitor_list = newlist

    def description(self, item):
        """
        Return the description of the item number (item)
        """
        return self.__get__(item, "description")

    def regex(self, item):
        """
        Return the regular expression of the item number (item)
        """
        return self.__get__(item, "regex")

    def command(self, item):
        """
        Return the stats command of the item number (item)
        """
        return self.__get__(item, "command")

    def countmin(self, item):
        """
        Return the minimum number of processes of the item number (item)
        """
        return self.__get__(item, "countmin")

    def countmax(self, item):
        """
        Return the maximum number of processes of the item number (item)
        """
        return self.__get__(item, "countmax")
