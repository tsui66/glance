#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

from oslo.config import cfg

from glance import manager
from glance.utils import importutils

rpcapi_opts = [
        cfg.StrOpt('GlanceAgentDriver',
                    default = 'glance.db.models',
                    help = 'The path of Glance Agent Driver module.'),
]

CONF =  cfg.CONF
CONF.register_opts(rpcapi_opts)

class GlancePushManager(manager.Manager):
    
    def __init__(self, *args, **kwargs):
        self.driver = importutils.import_module(CONF.GlanceAgentDriver)
        super(GlancePushManager, self).__init__(*args, **kwargs)

    def pushSystem(self, data, **kwargs):
        #server_key = data["server_key"]
        server_key = "0.0.0.0"

        self.driver.api_model.store_system_entries(server_key, data)

    def pushServer(self, data, **kwargs):
        name = data["hostname"]
        if self.driver.server_model.server_exists(name) == 1:
            return
        else:
            self.driver.server_model.add(data)

    def PushProcess(self, server_key, data, **kwargs):
        self.driver.api_model.store_process_entries(server_key, data)

    def PushPortScan(self, data, **kwargs):
        server_key = '0.0.0.0'
        data_dict = {}
        data_dict['host'] =  data['host']
        data_dict['scan'] =  data['scan']['scan'][data['host']]['tcp']
        self.driver.api_model.store_portscan_entries(server_key, data_dict)

    def PushTraffic(self, data, **kwargs):
        print 'enter %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        self.driver.traffic_model.add(data)
        print 'end'

    def PushUser(self, data, **kwargs):
        pass
