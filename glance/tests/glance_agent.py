#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-18
#Copyright 2013 nuoqingyun xuqifeng

import os
import sys
import unittest
import time
import multiprocessing

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
    sys.argv[0]), os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "glance", "__init__.py")):
    sys.path.insert(0, possible_topdir)

print possible_topdir
from glance.glance_agent.api import GlanceAgentAPI

class GlanceTestCase(unittest.TestCase):
        
    def setUp(self):
        self.api = GlanceAgentAPI()

    def tearDown(self):
        pass

    #def test_Glance_getSystem(self):
    #    system = self.api.getSystem()
    #    print system

    #def test_Glance_getServer(self):
    #    server_key = '0.0.0.0'
    #    server = self.api.getServer(server_key)
    #    print server

    #def test_Glances_getLoad(self):
    #    loadavg = self.api.getLoad()
    #    print loadavg

    #def test_Glances_getFs(self):
    #    Fs = self.api.getFs()
    #    print Fs
            
    #def test_Glances_getProcess(self):
    #    process = self.api.getProcess()
    #    print process

    #def test_Glances_getPortScan(self):
    #    portScan = self.api.getPortScan()
    #    print portScan

    def test_Glances_getTraffic(self):
        traffic = self.api.getTraffic()
        print traffic

if __name__ == '__main__':
    #time.clock()
    #CGroupTestSuite = unittest.TestSuite()
    #CGroupTestSuite.addTest(GlanceTestCase("test_enable"))
    #runner = unittest.TextTestRunner()
    #runner.run(CGroupTestSuite)    
    unittest.main()
