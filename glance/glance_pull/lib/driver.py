#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

from glance import log as logging 
from glance.glance_agent.lib import Glance
from glance.glance_agent.lib import GlanceNMAP
from glance.glance_agent.lib import GlanceTraffic

LOG = logging.getLogger(__name__)

stats = Glance.GlanceStats()
stats.update()
nma = GlanceNMAP.GlanceNMAP()
tra = GlanceTraffic.gatherlogdata

def getServer():
    return stats.getServer()

def getUptime():
    return stats.getUptime()

def getCore():
    return stats.getCore()

def getCpu():
    return stats.getCpu()

def getPerCpu():
    return stats.getPerCpu()

def getMem():
    return stats.getMem()

def getMemSwap():
    return stats.getMemSwap()

def getNetwork():
    return stats.getNetwork()

def getDiskIO():
    return stats.getDiskIO()

def getFs():
    return stats.getFs(
            )
def getProcess():

    stats.update()
    pc =  stats.getProcessCount()
    pl =  stats.getProcessList()
    return pc, pl

def getSensors():
    return stats.getSensors()

def getHDDTemp():
    return stats.getHDDTemp()

def getLoad():
    return stats.getLoad()

def getNow():
    return stats.getNow()

def getPortScan(callback=None):
    hosts = "192.168.1.247"
    ports = '80,81,22,21,5555,5500' 
    arguments = "-sV"
    nma.PortScannerAsync(hosts, ports, arguments, callback)

def getTraffic():
    return tra.gather_log()

