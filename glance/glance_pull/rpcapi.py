#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-8-27
#Copyright 2013 nuoqingyun xuqifeng

"""
Client side of the glancei pull RPC API
"""

from oslo.config import cfg

from glance.rpc.proxy import RpcProxy

pull_rpcapi_opts = [
        cfg.StrOpt('glance_topic',
                    default = 'glance_pull',
                    help = 'the topic glance nodes listen on'),
]

CONF =  cfg.CONF
CONF.register_opts(pull_rpcapi_opts)

def _get_topic(topic, host = None):
    '''Get the topic to use for a message.
    
    :param topic: the base topic
    :param host: explicit host to send the message to.
    
    :return: a topic string
    '''
    return "%s.%s" % (topic, host) if host else topic
        

class API(RpcProxy):
    """
    Client side of the glance api.
    API version history:
        1.0 - Initial version.
        1.1 - Rewrite glance,add port scan.
    """
    def __init__(self):
        self.host = "192.168.11.247"
        self.topic = CONF.glance_topic
        super(API, self).__init__(topic = CONF.glance_topic)

    def getSystem(self, charts, date_from, date_to, server, **kwargs):
        return self.call(self.make_msg('getSystem',
                                charts = charts,
                                date_from = date_from,
                                date_to = date_to,
                                server = server),
                topic = _get_topic(self.topic, self.host))

    def getServer(self, server, filter, **kwargs):
        return self.call(self.make_msg('getServer',
                server = server,
                filter = filter),
                topic = _get_topic(self.topic, self.host))

    def callLoad(self, **kwargs):
        self.cast(self.make_msg('getLoad'),
                topic = _get_topic(self.topic, self.host))

    def callCore(self, **kwargs):
        self.cast(self.make_msg('getCore'),
                topic = _get_topic(self.topic, self.host))

    def callPerCpu(self, **kwargs):
        self.cast(self.make_msg('getPerCpu'),
                topic = _get_topic(self.topic, self.host))

    def callMem(self, **kwargs):
        self.cast(self.make_msg('getMem'),
                topic = _get_topic(self.topic, self.host))

    def callMemSwap(self, **kwargs):
        self.cast(self.make_msg('getMemSwap'),
                topic = _get_topic(self.topic, self.host))

    def callNetwork(self, **kwargs):
        self.cast(self.make_msg('getNetwork'),
                topic = _get_topic(self.topic, self.host))

    def callDiskIO(self,  **kwargs):
        self.cast(self.make_msg('getDiskIO'),
                topic = _get_topic(self.topic, self.host))

    def callFs(self,  **kwargs):
        self.cast(self.make_msg('getFs'),
                topic = _get_topic(self.topic, self.host))

    def getProcess(self, server, date_to, **kwargs):
        return self.call(self.make_msg('getProcess', server = server, date_to = date_to, kwargs = kwargs),
                topic = _get_topic(self.topic, self.host))

    def callSensors(self, **kwargs):
        self.cast(self.make_msg('getSensors'),
                topic = _get_topic(self.topic, self.host))

    def callHDDTemp(self, **kwargs):
        self.cast(self.make_msg('getHDDTemp'),
                topic = _get_topic(self.topic, self.host))

    def getPortScan(self, server, **kwargs):
        return self.call(self.make_msg('getPortScan', server = server),
                topic = _get_topic(self.topic, self.host))

    def getTraffic(self, date, domain, **kwargs):
        return self.call(self.make_msg('getTraffic', date = date,
                        domain = domain),
                topic = _get_topic(self.topic, self.host))
