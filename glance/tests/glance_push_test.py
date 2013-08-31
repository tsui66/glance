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
from glance.glance_agent.manager import GlanceAgentManager

class GlanceTestCase(unittest.TestCase):
        
    def setUp(self):
        self.glanceapi = GlanceAgentManager()

    def tearDown(self):
        pass

    def test_Glance_pushSystem(self):
        data = {
                "key" : "0.0.0.0",
                "linux_distro" : "CntOS 6.4",
                "platform" : "32bit",
                "os_name" : "Linux",
                "os_version" : "2.6.32-358.e16.i686",
                "uptime" : "1 days 16 hours 16 minutes 29 seconds",
                "last_check" : 1373358415,
                "hostname" : "appengine",
                "notes" : "0.0.0.0",
                }
        self.glanceapi.getServer(data['key'])

    def test_Glances_pushServer(self):
        data = {
                "key" : "0.0.0.0",
                "linux_distro" : "CntOS 6.4",
                "platform" : "32bit",
                "os_name" : "Linux",
                "os_version" : "2.6.32-358.e16.i686",
                "uptime" : "1 days 16 hours 16 minutes 29 seconds",
                "last_check" : 1373358415,
                "hostname" : "appengine",
                "notes" : "0.0.0.0",
                }
        #self.glanceapi.getServer(data)
        
if __name__ == '__main__':
    #time.clock()
    #CGroupTestSuite = unittest.TestSuite()
    #CGroupTestSuite.addTest(GlanceTestCase("test_enable"))
    #runner = unittest.TextTestRunner()
    #runner.run(CGroupTestSuite)    
    unittest.main()
