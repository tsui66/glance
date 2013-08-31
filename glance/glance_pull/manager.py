#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import re
from oslo.config import cfg

from glance import manager
from glance.utils import importutils
#from glance.glance_pull import rpcapi

manager_opts = [
        cfg.StrOpt('GlanceDBDriver',
                    default = 'glance.db.models',
                    help = 'The path of Glance db Driver module.'),
]

CONF =  cfg.CONF
CONF.register_opts(manager_opts)

class GlancePullManager(manager.Manager):
    
    def __init__(self, *args, **kwargs):
        self.driver = importutils.import_module(CONF.GlanceDBDriver)
        #self.GlanceAPI = rpcapi.API()
        super(GlancePullManager, self).__init__(*args, **kwargs)

    def getSystem(self, charts, date_from, date_to, server, **kwargs):
        return  self.driver.system_model.get_system_data(charts, date_from, date_to, server)

    def getServer(self, server, filter, **kwargs):
        print 'getServer'
        if server:
            print 'getServer'
            return self.driver.server_model.get_server_by_key(server['key'])
        elif filter:
            print 'getServer'
            servers =  self.driver.server_model.get_filtered(filter)
            servers_dict = {}
            for server in servers.clone():
                id = str(server['_id'])
                del server['_id']
                servers_dict[id] = server

            return servers_dict
                
        else:
            print 'getServer'
            return self.driver.server_model.get_all_dict()
        

    def getCore(self, **kwargs):
        pass

    def getPerCpu(self, **kwargs):
        pass

    def getMem(self, **kwargs):
        pass

    def getMemSwap(self, **kwargs):
        pass

    def getNetwork(self, **kwargs):
        pass

    def getDiskIO(self, **kwargs):
        pass

    def getFs(self, **kwargs):
        pass

    def getProcess(self, server, date_to, **kwargs):
        return self.driver.process_model.get_server_processes(server,  date_to)

    def getSensors(self, **kwargs):
        pass

    def getHDDTemp(self, **kwargs):
        pass

    def getPortScan(self, server, **kwargs):
        if server:
            portscan = self.driver.portscan_model.get_portstate_by_domainlist(server)
            return portscan
        else:
            portscan = self.driver.portscan_model.get_all()
            return portscan

    def getTraffic(self, date, domain, **kwargs):
        return self.driver.traffic_model.get_traffic_by_domain(date, domain)
