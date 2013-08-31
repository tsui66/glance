#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-8-27
#Copyright 2013 nuoqingyun xuqifeng

"""
Client side of the glance API
"""

from oslo.config import cfg

from glance.glance_pull import rpcapi


class GlancePullAPI(object):
    """
    Client side of the glance api.
    API version history:
        1.0 - Initial version.
        1.1 - Rewrite glance,add port scan.
    """
    def __init__(self):
        self.GlanceAPI = rpcapi.API() 
        super(GlancePullAPI, self).__init__()

    def getSystem(self, charts, date_from, date_to, server, **kwargs):
        return self.GlanceAPI.getSystem(charts, date_from, date_to, server, **kwargs)

    def getServer(self, server=None, filter=None, **kwargs):
        return self.GlanceAPI.getServer(server, filter, **kwargs)

    def getLoad(self):
        self.GlanceAPI.callLoad()

    def getCore(self, **kwargs):
        self.GlanceAPI.callCore()

    def getPerCpu(self, **kwargs):
        self.GlanceAPI.callPerCpu()

    def getMem(self, **kwargs):
        self.GlanceAPI.callMem()
        
    def getMemSwap(self, **kwargs):
        self.GlanceAPI.callMemSwap()

    def getNetwork(self, **kwargs):
        self.GlanceAPI.callNetwork()

    def getDiskIO(self, **kwargs):
        self.GlanceAPI.callDiskIO()

    def getFs(self, **kwargs):
        self.GlanceAPI.callFs()

    def getProcess(self, server, date_to, **kwargs):
        return self.GlanceAPI.getProcess(server, date_to)

    def getSensors(self, **kwargs):
        self.GlanceAPI.callSensors()

    def getHDDTemp(self, **kwargs):
        self.GlanceAPI.callHDDTemp()

    def getPortScan(self, server, **kwargs):
        return self.GlanceAPI.getPortScan(server, **kwargs)

    def getTraffic(self, date, domain=None, **kwargs):
        print "getTraffic"
        return self.GlanceAPI.getTraffic(date, domain)

