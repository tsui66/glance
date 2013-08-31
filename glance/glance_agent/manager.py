#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import re
from oslo.config import cfg

from glance import manager
from glance.utils import importutils
from glance.glance_agent import rpcapi

rpcapi_opts = [
        cfg.StrOpt('GlanceAgentDriver',
                    default = 'glance.glance_agent.lib.driver',
                    help = 'The path of Glance Agent Driver module.'),
        cfg.ListOpt('GlanceSystemList',
                    default = ['cpu', 'memory', 'network', 'disk', 'loadavg'],
                    help = 'The list of system to glance.'),
        cfg.ListOpt('regex',
                    default = ['rabbitmq', 'cgroup', 'nginx', 'mongod'],
                    help = 'The list of process to be monitor'),
]

CONF =  cfg.CONF
CONF.register_opts(rpcapi_opts)
#CONF.import_opt('GlanceSystemList', 'glance'

class GlanceAgentManager(manager.Manager):
    
    def __init__(self, *args, **kwargs):
        self.regexlist = CONF.regex
        self.driver = importutils.import_module(CONF.GlanceAgentDriver)
        self.GlanceAPI = rpcapi.API()
        self.GlanceSystemList = CONF.GlanceSystemList
        self.uptime = self.driver.getUptime()
        self.lastcheck = self.driver.getNow()
        super(GlanceAgentManager, self).__init__(*args, **kwargs)

    def getSystem(self, **kwargs):
        data = {}
        if 'cpu' in self.GlanceSystemList:
            cpu = self.driver.getCpu()
            data['cpu'] = cpu
        if 'memory' in self.GlanceSystemList:
            memory = self.driver.getMem()
            memswap = self.driver.getMemSwap()
            data['memory'] = memory
            data['memswap'] = memswap
        if 'network' in self.GlanceSystemList:
            network = self.driver.getNetwork()
            data['network'] = network
        if 'disk' in self.GlanceSystemList:
            disk = self.driver.getFs()
            data['disk'] = disk
        if 'loadavg' in self.GlanceSystemList:
            loadavg = self.driver.getLoad()
            data['loadavg'] = loadavg
        data['uptime'] = self.uptime
        data['last_check'] = self.lastcheck
        self.GlanceAPI.getSystem(data = data) 

    def getServer(self, server_key, **kwargs):
        data = {}
        data['key'] = server_key
        data['uptime'] = self.uptime
        data['last_check'] = self.lastcheck
        data.update(self.driver.getServer())
        self.GlanceAPI.getServer(data = data) 

    def getCore(self, **kwargs):
        data = self.driver.getCore()
        self.GlanceAPI.getCore(data = data) 

    def getPerCpu(self, **kwargs):
        data = self.driver.getPerCpu()
        self.GlanceAPI.getPerCpu(data = data) 

    def getMem(self, **kwargs):
        data = self.driver.getMem()
        self.GlanceAPI.getMem(data = data) 

    def getMemSwap(self, **kwargs):
        data = self.getMemSwap()
        self.GlanceAPI.getMemSwap(data = data) 

    def getNetwork(self, **kwargs):
        data = self.driver.getNetwork()
        self.GlanceAPI.getNetwork(data = data) 

    def getDiskIO(self, **kwargs):
        data = self.driver.getDiskIO()
        self.GlanceAPI.getDiskIO(data = data) 

    def getFs(self, **kwargs):
        data = self.driver.getFs()
        self.GlanceAPI.getFs(data = data) 

    def getProcess(self, server_key, **kwargs):
        pc, pl = self.driver.getProcess()
        data = pl
        data_list = []
        regexlist = CONF.regex[:]
        regexstr = regexlist[0]
        del regexlist[0]
        for s in regexlist:
            regexstr += "|%s" % s
        regex = '/' + regexstr + '/'
        for p in data:
            if re.search(regex, p['cmdline']):
                data_list.append(p)
        self.GlanceAPI.getProcess(server_key = server_key, data = data_list) 

    def getSensors(self, **kwargs):
        data = self.driver.getSensors()
        self.GlanceAPI.getSensors(data = data) 

    def getHDDTemp(self, **kwargs):
        data = self.driver.getHDDTemp()
        self.GlanceAPI.getHDDTemp(data = data) 

    def getPortScan(self, **kwargs):
        def callback_result(host, scan_result):
            data = {'host':host, 'scan': scan_result}
            self.GlanceAPI.getPortScan(data = data) 

        self.driver.getPortScan(callback = callback_result)

    def getTraffic(self, **kwargs):
        self.driver.getTraffic(self.GlanceAPI)
        #self.GlanceAPI.getTraffic()
