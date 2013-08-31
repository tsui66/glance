#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import nmap
from oslo.config import cfg

from glance import log as logging

glance_opts = [
        cfg.IntOpt('ScanTime',
                    default = 2,
                    help = 'Wait for the current scan process to finish, or timeout'),
]

CONF = cfg.CONF
CONF.register_opts(glance_opts)

LOG = logging.getLogger(__name__)

class GlanceNMAP(object):

    def __init__(self):
        self.nma = nmap.PortScannerAsync()
        super(GlanceNMAP, self).__init__()

    def PortScannerAsync(self, hosts='127.0.0.1', ports=None, arguments=None, callback=None):
        '''Scan given hosts in a separate process and return host by host result using callback function.
        :param hosts: string for hosts as nmap use it 'scanme.nmap.org' or '198.116.0-255.1-127' or '216.163.128.20/20'.
        :param ports: string for ports as nmap use it '22,53,110,143-4564'.
        :param arguments: string of arguments for nmap '-sU -sX -sC'.
        :param callback: callback function which takes (host, scan_data) as arguments.

        :returns: None
        '''
        print "PortScannerAsync"
        self.nma.scan(hosts, ports, arguments, callback)
        while self.ma.still_scanning():
            self.nma.wait(CONF.ScanTime)

