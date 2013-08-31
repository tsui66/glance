#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-8-19
#Copyright 2013 nuoqingyun xuqifeng

"""
Client side of the glance API
"""

from oslo.config import cfg

from glance.glance_agent import rpcapi
from glance import log as logging

LOG = logging.getLogger(__name__)

class GlanceAgentAPI(object):
    """
    Client side of the glance api.
    API version history:
        1.0 - Initial version.
        1.1 - Rewrite glance,add port scan.
    """
    def __init__(self):
        self.GlanceAPI = rpcapi.API() 
        super(GlanceAgentAPI, self).__init__()

    def getSystem(self):
        self.GlanceAPI.callSystem()

    def getServer(self, server_key):
        self.GlanceAPI.callServer(server_key)

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

    def getProcess(self, server_key, **kwargs):
        self.GlanceAPI.callProcess(server_key)

    def getSensors(self, **kwargs):
        self.GlanceAPI.callSensors()

    def getHDDTemp(self, **kwargs):
        self.GlanceAPI.callHDDTemp()

    def getPortScan(self, **kwargs):
        self.GlanceAPI.callPortScan()

    def getTraffic(self, **kwargs):
        print "getTraffic"
        self.GlanceAPI.callTraffic()

