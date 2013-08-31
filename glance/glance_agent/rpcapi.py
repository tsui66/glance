#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-8-19
#Copyright 2013 nuoqingyun xuqifeng

"""
Client side of the glance RPC API
"""

from oslo.config import cfg

from glance.rpc.proxy import RpcProxy

rpcapi_opts = [
        cfg.StrOpt('glance_topic',
                    default = 'glance_agent',
                    help = 'the topic glance nodes listen on'),
        cfg.StrOpt('glance_push_topic',
                    default = 'glance_push',
                    help = 'the topic glance push nodes listen on'),
]

CONF =  cfg.CONF
CONF.register_opts(rpcapi_opts)

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
        self.push_topic = CONF.glance_push_topic
        super(API, self).__init__(topic = CONF.glance_topic)

    def callSystem(self, **kwargs):
        self.cast(self.make_msg('getSystem'),
                topic = _get_topic(self.topic, self.host))

    def callServer(self, server_key, **kwargs):
        self.cast(self.make_msg('getServer',
                server_key = server_key),
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

    def callProcess(self, server_key, **kwargs):
        self.cast(self.make_msg('getProcess', server_key = server_key),
                topic = _get_topic(self.topic, self.host))

    def callSensors(self, **kwargs):
        self.cast(self.make_msg('getSensors'),
                topic = _get_topic(self.topic, self.host))

    def callHDDTemp(self, **kwargs):
        self.cast(self.make_msg('getHDDTemp'),
                topic = _get_topic(self.topic, self.host))

    def callPortScan(self, **kwargs):
        self.cast(self.make_msg('getPortScan'),
                topic = _get_topic(self.topic, self.host))

    def callTraffic(self, **kwargs):
        print "enter callTraffic"
        self.cast(self.make_msg('getTraffic'),
                topic = _get_topic(self.topic, self.host))

#class PushAPI(RpcProxy):
#    """
#    Client side of the glance push api.
#    API version history:
#        1.0 - Initial version.
#        1.1 - Rewrite glance,add port scan.
#    """
#   def __init__(self):
#        self.host = "192.168.1.247"
#        self.push_topic = CONF.glance_push_topic
#        super(PushAPI, self).__init__(topic = self.push_topic)

    def getSystem(self, data, **kwargs):
        self.cast(self.make_msg('pushSystem', data = data),
                topic = _get_topic(self.push_topic, self.host))

    def getServer(self, data, **kwargs):
        print "rpc getServer"
        self.cast(self.make_msg('pushServer', data = data),
                topic = _get_topic(self.push_topic, self.host))

    def getCore(self, data, **kwargs):
        self.cast(self.make_msg('Core', data = data),
                topic = _get_topic(self.topic, self.host))

    def getPerCpu(self, data, **kwargs):
        self.cast(self.make_msg('PerCpu', data = data),
                topic = _get_topic(self.topic, self.host))

    def getMem(self, data, **kwargs):
        self.cast(self.make_msg('Memory', data = data),
                topic = _get_topic(self.topic, self.host))

    def getMemSwap(self, data, **kwargs):
        self.cast(self.make_msg('MemSwap', data = data),
                topic = _get_topic(self.topic, self.host))

    def getNetwork(self, data, **kwargs):
        self.cast(self.make_msg('Network', data = data),
                topic = _get_topic(self.topic, self.host))

    def getDiskIO(self, data, **kwargs):
        self.cast(self.make_msg('DiskIO', data = data),
                topic = _get_topic(self.topic, self.host))

    def getFs(self, data, **kwargs):
        self.cast(self.make_msg('FileSystem', data = data),
                topic = _get_topic(self.topic, self.host))

    def getProcess(self, server_key, data, **kwargs):
        self.cast(self.make_msg('PushProcess', 
                                server_key = server_key, 
                                data = data),
                topic = _get_topic(self.push_topic, self.host))

    def getSensors(self, data, **kwargs):
        self.cast(self.make_msg('Sensors', data = data),
                topic = _get_topic(self.topic, self.host))

    def getHDDTemp(self, data, **kwargs):
        self.cast(self.make_msg('HDDTemp', data = data),
                topic = _get_topic(self.topic, self.host))

    def getPortScan(self, data, **kwargs):
        self.cast(self.make_msg('PushPortScan', data = data),
                topic = _get_topic(self.push_topic, self.host))

    def getTraffic(self, data, **kwargs):
        print "enter getTraffic"
        self.cast(self.make_msg('PushTraffic', data = data),
                topic = _get_topic(self.push_topic, self.host))
