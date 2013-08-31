#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-28
#Copyright 2013 nuoqingyun xuqifeng

import os
import sys
import unittest

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
    sys.argv[0]), os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "glance", "__init__.py")):
    sys.path.insert(0, possible_topdir)
print possible_topdir
from glance.db.models import traffic_model

class GlanceDBCase(unittest.TestCase):
        
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Glances_updateTraffic(self):
        traffic = traffic_model.update_traffic_detail_by_time()
        print traffic

if __name__ == '__main__':
    #time.clock()
    #CGroupTestSuite = unittest.TestSuite()
    #CGroupTestSuite.addTest(GlanceTestCase("test_enable"))
    #runner = unittest.TextTestRunner()
    #runner.run(CGroupTestSuite)    
    unittest.main()
