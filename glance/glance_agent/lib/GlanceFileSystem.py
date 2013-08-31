#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import sys

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
    LOG.warning("psutil.virtual_memory() not available from psutil >= 0.6")
    psutil_mem_vm = False
else:
    psutil_mem_vm = True

try:
    # psutil.net_io_counters() only available from psutil >= 1.0.0
    psutil.net_io_counters()
except Exception:
    LOG.warning("psutil.net_io_counters() only available from psutil >= 1.0.0")
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
class glancesGrabFs:
    """
    Get FS stats
    """

    def __init__(self):
        """
        Init FS stats
        """

        # Ignore the following FS name
        self.ignore_fsname = ('', 'cgroup', 'fusectl', 'gvfs-fuse-daemon',
                              'gvfsd-fuse', 'none')

        # Ignore the following FS type
        self.ignore_fstype = ('autofs', 'binfmt_misc', 'configfs', 'debugfs',
                              'devfs', 'devpts', 'devtmpfs', 'hugetlbfs',
                              'iso9660', 'linprocfs', 'mqueue', 'none',
                              'proc', 'procfs', 'pstore', 'rootfs',
                              'securityfs', 'sysfs', 'usbfs')

        # ignore FS by mount point
        self.ignore_mntpoint = ('', '/dev/shm', '/lib/init/rw', '/sys/fs/cgroup')

    def __update__(self):
        """
        Update the stats
        """

        # Reset the list
        self.fs_list = []

        # Open the current mounted FS
        fs_stat = psutil.disk_partitions(all=True)
        for fs in range(len(fs_stat)):
            fs_current = {}
            fs_current['device_name'] = fs_stat[fs].device
            if fs_current['device_name'] in self.ignore_fsname:
                continue
            fs_current['fs_type'] = fs_stat[fs].fstype
            if fs_current['fs_type'] in self.ignore_fstype:
                continue
            fs_current['mnt_point'] = fs_stat[fs].mountpoint
            if fs_current['mnt_point'] in self.ignore_mntpoint:
                continue
            try:
                fs_usage = psutil.disk_usage(fs_current['mnt_point'])
            except Exception as e:
                LOG.warning(str(e))
                continue
            fs_current['size'] = fs_usage.total
            fs_current['used'] = fs_usage.used
            fs_current['avail'] = fs_usage.free
            self.fs_list.append(fs_current)

    def get(self):
        self.__update__()
        return self.fs_list
