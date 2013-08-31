#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


from oslo.config import cfg

from glance.utils import importutils


rpc_opts = [
        cfg.IntOpt('rpc_thread_pool_size',
                default=64,
                help=""),
        cfg.StrOpt('rpc_backend',
                default="%s.impl_kombu" % __package__,
                help="the MQ to user"),
        cfg.IntOpt('rpc_conn_pool_size',
                default=30,
                help="" ),
        cfg.StrOpt('control_exchange',
                default='glance',
                help=""),
        cfg.BoolOpt('fake_rabbit',
                default=False,
                help=""),
        cfg.IntOpt('rpc_response_timeout',
                default=60,
                help=""),
            ]
cfg.CONF.register_opts(rpc_opts)


def create_connection(new=True):
    """
    Create a connection to MQ
    """
    return _get_impl().create_connection(cfg.CONF, new=new)

def call(topic, msg, timeout=None):
    """
    Invoke a remote method and wait for return
    """
    return _get_impl().call(cfg.CONF, topic, msg, timeout)

def cast(topic, msg):
    """
    Invoke a remote method without wait for return
    """

    return _get_impl().cast(cfg.CONF, topic, msg)

def fanout_cast(topic, msg):
    """
    Broadcast a remote method with no return
    """
    return _get_impl().fanout_cast(cfg.CONF, topic, msg)

def multicall(topic, msg, timeout=None):
    """
    Invoke a remote method and get back an iterator
    """
    return _get_impl().multicall(cfg.CONF, topic, msg, timeout)

def notify(topic, msg):
    """
    Send notification event.
    """
    return _get_impl().notify(cfg.CONF, topic, msg)

def cleanup():
    """
    Clean up resource in use by implementation
    """
    return _get_impl().cleanup()

def cast_to_server(server_params, topic, msg):
    """
    Invoke a remote method that does not return anything
    """
    return _get_impl().cast_to_server(cfg.CONF, server_params, topic, msg)

def fanout_cast_to_server(server_params, topic, msg):
    """
    Broadcast to a remote method invocation with no return
    """
    return _get_impl().cast_to_server(cfg.CONF, server_params, topic, msg)

def queue_get_for(topic, host):
    """
    Get a queue name for given topic and host
    """

    return '%s.%s' %(topic, host) if host else topic

_RPCIMPL = None

def _get_impl():
    
    """
    Get the RPC backend
    """
    global _RPCIMPL
    if _RPCIMPL is None:
        try:
#TODO
            _RPCIMPL = importutils.import_module(cfg.CONF.rpc_backend)
        except ImportError:
            impl = "glance.rpc.impl_kombu"
            _RPCIMPL = importutils.import_module(impl)

    return _RPCIMPL
