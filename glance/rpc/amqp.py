#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import inspect
import logging
import sys
import uuid

from eventlet import greenpool
from eventlet import pools
from eventlet import semaphore

from glance.rpc import common as rpc_common
from glance.utils import networkutils


class Pool(pools.Pool):
    """
    """

    def __init__(self, conf, connection_cls, *args, **kwargs):

        self.connection_cls = connection_cls
        self.conf = conf
        kwargs.setdefault("max_size", self.conf.rpc_conn_pool_size)
        kwargs.setdefault("order_as_stack", True)
        super(Pool, self).__init__(*args, **kwargs)

    def create(self):
        """
        In the pool create new connection
        """
        return self.connection_cls(self.conf)

    def empty(self):
        """
        Empty the pool
        """
        while self.free_items:
            self.get().close()


_pool_create_sem = semaphore.Semaphore()

def get_connection_pool(conf, connection_cls):
    with _pool_create_sem:
        if not connection_cls.pool:
            connection_cls.pool = Pool(conf, connection_cls)
        return connection_cls.pool



class ConnectionContext(rpc_common.Connection):
    def __init__(self, conf, connection_pool, pooled = True, server_params = None):
        self.connection = None
        self.conf = conf
        self.connection_pool = connection_pool

        if pooled:
            self.connection = self.connection_pool.get()
        else:
            self.connection = connection_pool.connection_cls(conf,
                server_params = server_params)

        self.pooled = pooled

    def __enter__(self):
        return self

    def _done(self):
        if self.connection:
            if self.pooled:
                self.connection.reset()
                self.connection_pool.put(self.connection)
            else:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.connection = None

    def __exit__(self, exc_type, exc_value, tb):
        self._done()

    def __del__(self):
        self._done()

    def close(self):
        self._done()

    def create_consumer(self, topic, proxy, fanout = False):
        self.connection.create_consumer(topic, proxy, fanout)

    def create_worker(self, topic, proxy, pool_name):
        self.connection.create_consumer(topic, proxy, pool_name)

    def consumer_in_thread(self):
        self.connection.consumer_in_thread()

    def __getattr__(self, key):

        if self.connection:
            return getattr(self.connection, key)
        else:
            raise rpc_common.InvalidRPCConnectionReuse()


class RpcReplyContext(object):
    def __init__(self, **kwargs):
        self.msg_id = kwargs.pop('_msg_id', None)
        self.conf = kwargs.pop('conf')
        self.values = kwargs

    def deepcopy(self):
        values = copy.deepcopy(self.values)
        values['conf'] = self.conf
        values['msg_id'] = self.msg_id

        return self.__class__(**values)

    def reply(self, reply = None, failure = None, ending = False,
                connection_pool = None):
        if self.msg_id:
            msg_reply(self.conf, self.msg_id, connection_pool, reply, failure,
                    ending)

            if ending:
                self.msg_id = None

def msg_reply(conf, msg_id, connection_pool, reply = None,
                failure = None, ending = False):

    with ConnectionContext(conf, connection_pool) as conn:
        if failure:
            pass
        try:
            msg = {'result': reply, 'failure': failure}
        except TypeError:
            pass

        if ending:
            msg['ending'] = True
        conn.direct_send(msg_id, msg)

def pack_context(msg):
    pass

def unpack_context(conf, msg):
    pass

class ProxyCallback(object):
    """
    Calls method on a proxy object based on method and args
    """

    def __init__(self, conf, proxy, connection_pool):
        self.proxy = proxy
        self.pool = greenpool.GreenPool(conf.rpc_thread_pool_size)
        self.connection_pool = connection_pool
        self.conf = conf

    def __call__(self, message_data):
        """
        """
        method = message_data.get('method')
        args = message_data.get('args', {})
        ctxt = RpcReplyContext(conf = self.conf, **message_data)

        if not method:
            #ctxt.reply("No method for message: '%s'" % message_data,
                        #connection_pool=self.connection_pool)
            return
        #self.pool.spawn_n(self._process_data, method, ctxt, args)
        self.pool.spawn_n(self._process_data, method, args, ctxt)

    def _process_data(self, method, args, ctxt):
        """
        Process a message in a new thread
        """
        try:
            rval = self.proxy.dispatch(method, **args)
            if inspect.isgenerator(rval):
                for x in rval:
                    ctxt.reply(x, None, connection_pool = self.connection_pool)
            else:
                ctxt.reply(rval, None, connection_pool = self.connection_pool)
            ctxt.reply(ending = True, connection_pool = self.connection_pool)
        except Exception as e:
            ctxt.reply(None, sys.exc_info(),
                        connection_pool = self.connection_pool)



class MulticallWaiter(object):
    def __init__(self, conf, connection, timeout):
        self._connection = connection
        self._iterator = connection.iterconsume(timeout = timeout or conf.rpc_response_timeout)

        self._result = None
        self._done = False
        self._got_ending = False
        self._conf = conf

    def done(self):
        #print "enter done", self._connection, self._iterator,
        if self._done:
            return
        self._done = True
        self._iterator.close()
        self._iterator = None
        self._connection.close()

    def __call__(self, data):
        """
        the consume() callback will call this, Store the result.
        """

        if data['failure']:
            failure = data['failure']
            self._result = rpc_common.deserialize_remote_exception(self._conf, failure)
        elif data.get('ending', False):
            self._got_ending = True
        else:
            self._result = data['result']

    def __iter__(self):
        """
        Return a result until we get a None response from consumer
        """

        if self._done:
            raise StopIteration
        while 1:
            #print "enter __iter__"
            try:
                self._iterator.next()
            except Exception:
#TODO
                self.done()
            if self._got_ending:
                self.done()
                raise StopIteration
            result = self._result
            if isinstance(result, Exception):
                self.done()
                raise result
            yield result

def create_connection(conf, new, connection_pool):
    return ConnectionContext(conf, connection_pool, pooled = not new)

def multicall(conf, topic, msg, timeout, connection_pool):
    msg_id = uuid.uuid4().hex
    msg.update({'_msg_id': msg_id})

    pack_context(msg)
    conn = ConnectionContext(conf, connection_pool)
    wait_msg = MulticallWaiter(conf, conn, timeout)
    conn.declare_direct_consumer(msg_id, wait_msg)
    conn.topic_send(topic, msg)

    return wait_msg

def call(conf, topic, msg, timeout, connection_pool):
    rv = multicall(conf, topic, msg, timeout, connection_pool)

    rv = list(rv)
    if not rv:
        return
    return rv[-1]

def cast(conf, topic, msg, connection_pool):
    pack_context(msg)
    with ConnectionContext(conf, connection_pool) as conn:
        conn.topic_send(topic, msg)


def fanout_cast(conf, topic, msg, connection_pool):
    pack_context(msg)
    with ConnectionContext(conf, connection_pool) as conn:
        conn.fanout_send(topic, msg)


def cast_to_server(conf, server_params, topic, msg, connection_pool):
    pack_context(msg)
    with ConnectionContext(conf, connection_pool, pooled = False,
                        server_params = server_params) as conn:
        conn.topic_send(topic, msg)


def fanout_cast_to_server(conf, server_params, topic, msg, connection_pool):
    pack_context(msg)
    with ConnectionContext(conf, connection_pool, pooled = False,
                        server_params = server_params) as conn:
        conn.fanout_send(topic, msg)

def notify(conf, topic, msg, connection_pool):
    event_type = msg.get('event_type')
    pack_context(msg)

    with ConnectionContext(conf, connection_pool) as conn:
        conn.notify_send(topic, msg)

def cleanup(connection_pool):
    if connection_pool:
        connection_pool.empty()

def get_control_exchange(conf):
    try:
        return conf.control_exchange
    except conf.NoSuchOptError:
        return "No Such Opt Error"
