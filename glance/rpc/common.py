#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import copy
import logging
import traceback


class RPCException(Exception):
    message = "An Unknown RPC related exception occurred"

    def __init__(self, message = None, **kwargs):
        self.kwargs = kwargs

        if not message:
            try:
                message = self.message % kwargs
            except Exception as e:
                message = self.message

        super(RPCException, self).__init__(message)


class RemoteError(RPCException):

    message = "Remote error: %(exc_type)s %(value)s\n%(traceback)s"

    def __init__(self, exc_type = None, value = None, traceback = None):
        self.exc_type = exc_type
        self.value = value
        self.traceback = traceback
        super(RemoteError, self).__init__(exc_type = exc_type,
                                            value = value,
                                            traceback = traceback)


class Timeout(RPCException):
    """
    """
    message = "Timeout while waiting on RPC response"



class InvalidRPCConnectionReuse(RPCException):

    message = "Invalid reuse of an RPC Connection"

class Connection(object):

    def close(self):

        raise NotImplementedError()

    def create_consumer(self, topic, proxy, fanout = False):

        raise NotImplementedError()

    def create_worker(self, topic, proxy, pool_name):
        raise NotImplementedError()

    def consumer_in_thread(self):

        raise NotImplementedError()

def _sage_log(log_func, mes, msg_data):
    """
    """
    pass

def serialize_remote_exception(failure_info):
    """
    """
    pass

def deserialize_remote_exception(conf, data):
    """
    """
    pass
