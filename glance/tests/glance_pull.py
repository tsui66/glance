#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-18
#Copyright 2013 nuoqingyun xuqifeng

import os
import sys
import unittest

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
    sys.argv[0]), os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "glance", "__init__.py")):
    sys.path.insert(0, possible_topdir)

print possible_topdir
from glance.glance_pull.api import GlancePullAPI

class GlanceTestCase(unittest.TestCase):
        
    def setUp(self):
        self.api = GlancePullAPI()

    def tearDown(self):
        pass

    #def test_Glance_getSystem(self):
    #    charts = ['memory', 'cpu', 'disk', 'network', 'loadavg']
    #    date_to = 1377324487
    #    date_from = 1377324526
    #    server = {'key':'0.0.0.0'}
    #    system = self.api.getSystem(charts, date_from, date_to, server)
    #    print system

    #def test_Glance_getServer(self):
    #    server_key = '0.0.0.0'
    #    filter = [{'_id': '52184dc6d0e96f1bdf667a4b'}]
    #    server = self.api.getServer(filter=filter)
        #server = self.api.getServer()
    #    print server

    #def test_Glances_getLoad(self):
    #    loadavg = self.api.getLoad()
    #    print loadavg

    #def test_Glances_getFs(self):
    #    Fs = self.api.getFs()
    #    print Fs
            
    #def test_Glances_getProcess(self):
    #    server = {'key': '0.0.0.0'}
    #    date_to = 1377666446
    #    process = self.api.getProcess(server, date_to)
    #    print process

    #def test_Glances_getPortScan(self):
    #    server =[{'key':'0.0.0.0'}]
    #    portScan = self.api.getPortScan(server)
    #    print portScan

    def test_Glances_getTraffic(self):
        date = 'day'
        domain = 'www.sscnfs.com'
        traffic = self.api.getTraffic(date, domain)
        print traffic

if __name__ == '__main__':
    #time.clock()
    #CGroupTestSuite = unittest.TestSuite()
    #CGroupTestSuite.addTest(GlanceTestCase("test_enable"))
    #runner = unittest.TextTestRunner()
    #runner.run(CGroupTestSuite)    
    unittest.main()
