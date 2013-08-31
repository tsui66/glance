#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


from glance import rpc


class RpcProxy(object):
    
    def __init__(self, topic):
        self.topic = topic
        super(RpcProxy,self).__init__()

    def _get_topic(self, topic):
        """
        Return the topic for use for a message
        """
        return topic if topic else self.topic

    @staticmethod
    def make_msg(method, **kwargs):
        return {'method': method, 'args': kwargs}

    def call(self, msg, topic=None, timeout=None):
        """
        rpc.call() a remote method

        msg: come from up method make_msg contain method, args
        topic: Override the topic for this message
        timeout: a timeout for use to wait ing a response
        """

        return rpc.call( self._get_topic(topic), msg, timeout)

    def multicall(self, msg, topic=None, timeout=None):
        """
        rpc.multicall() a remote method
        msg: come from up method make_msg  contain method, args
        topic: Override the topic for this message
        timeoutL fro wait for a response timeout

        return  An iterator that lets you process each of the retured values from the   
            remote method as they arrive.
        """

        return rpc.multicall(self._get_topic(topic), msg, timeout)
    
    def cast(self, msg, topic=None):
        """
        rpc.cast() for a remote method
        msg: come from up method make_msg, contain method, args
        topic: Override the topic for this topic
        """
        print "=========================", topic, "rpc cast"
        rpc.cast(self._get_topic(topic), msg)

    def fanout_cast(self, msg, topic=None):
        """
        rpc.fanout_cast() for a remote method

        msg: come from up method make_msg, contain method, args
        topic: Override the topic for this topic
        """

        rpc.fanout_cast(self._get_topic(topic), msg)

    def fanout_cast_to_server(self, server_params, msg, topic=None):
        """
        rpc.fanout_cast_to_server() for a remote method

        server_params: Server parameters
        msg:
        topic:
        """

        rpc.fanout_cast_to_server(server_params, self._get_topic(topic), msg)
