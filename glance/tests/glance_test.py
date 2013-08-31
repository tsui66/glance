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
from glance.glance_agent.lib import Glance

class GlanceTestCase(unittest.TestCase):
        
    def setUp(self):
        self.stats = Glance.GlanceStats()
        self.stats.update()

    def tearDown(self):
        pass

    def test_Glance_getSystem(self):
        system = self.stats.getSystem()
        print system
        
    def test_Glances_getCore(self):
        self.stats.update()
        core = self.stats.getCore()
        print("CPU Core number: %s" % core)
        self.assertTrue(type(core) == int)
        self.assertEqual(core, multiprocessing.cpu_count())

    def test_Glances_getCpu(self):
        self.stats.update()
        cpu = self.stats.getCpu()
        print("CPU stat %s:" % cpu)
        self.assertTrue(type(cpu) == dict)
        self.assertTrue(len(cpu) > 1)

    def test_Glances_getPerCpu(self):
        self.stats.update()
        percpu = self.stats.getPerCpu()
        print("PerCPU stat %s:" % percpu)
        self.assertTrue(type(percpu) == list)
        self.assertEqual(len(percpu), multiprocessing.cpu_count())

    def test_Glances_getMem(self):
        self.stats.update()
        mem = self.stats.getMem()
        print("Mem stat %s:" % mem)
        self.assertTrue(type(mem) == dict)
        self.assertTrue(len(mem) > 2)

    def test_Glances_getMemSwap(self):
        self.stats.update()
        memswap = self.stats.getMemSwap()
        print("MemSwap stat %s:" % memswap)
        self.assertTrue(type(memswap) == dict)
        self.assertTrue(len(memswap) > 2)

    def test_Glances_getNetwork(self):
        self.stats.update()
        net = self.stats.getNetwork()
        print("Network stat %s:" % net)
        self.assertTrue(type(net) == list)
        self.assertTrue(len(net) > 0)

    def test_Glances_getLoad(self):
        self.stats.update()
        load = self.stats.getLoad()
        print("Load stat %s:" % load)
        ##self.assertTrue(type(net) == list)
        #self.assertTrue(len(net) > 0)

    def test_Glances_getDiskIO(self):
        self.stats.update()
        diskio = self.stats.getDiskIO()
        print("DiskIO stat %s:" % diskio)
        self.assertTrue(type(diskio) == list)
        self.assertTrue(len(diskio) > 0)

    def test_Glances_getFs(self):
        self.stats.update()
        fs = self.stats.getFs()
        print("File system stat %s:" % fs)
        self.assertTrue(type(fs) == list)
        self.assertTrue(len(fs) > 0)

    def test_Glances_getProcess(self):
        self.stats.update()
        pc = self.stats.getProcessCount()
        pl = self.stats.getProcessList()
        #print("Processes stat %s:" % pc)
        print("Processes list %s:" % pl)
        self.assertTrue(type(pc) == dict)
        self.assertTrue(len(pc) > 2)
        self.assertTrue(type(pl) == list)
        self.assertTrue(len(pl) > 0)

    def test_Glances_getSensors(self):
        self.stats.update()
        sensors = self.stats.getSensors()
        print("Optionnal sensors stat %s:" % sensors)
        self.assertTrue(type(sensors) == list)
        #~ self.assertTrue(len(sensors) > 0)

    def test_Glances_getHDDTemp(self):
        self.stats.update()
        hddtemp = self.stats.getHDDTemp()
        print("Optionnal hddtemp stat %s:" % hddtemp)
        self.assertTrue(type(hddtemp) == list)
        #~ self.assertTrue(len(hddtemp) > 0)
        
    def test_Glances_getPortScan(self):
        self.stats.update()
        portscan = self.stats.getPortScan('192.168.1.247', '80')
        print("Optionnal hddtemp stat %s:" % portscan)
        self.assertTrue(type(portscan) == list)

if __name__ == '__main__':
    #time.clock()
    #CGroupTestSuite = unittest.TestSuite()
    #CGroupTestSuite.addTest(GlanceTestCase("test_enable"))
    #runner = unittest.TextTestRunner()
    #runner.run(CGroupTestSuite)    
    unittest.main()
