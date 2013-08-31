#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng



import eventlet
import functools
import greenlet
import itertools
import kombu
import kombu.connection
import kombu.entity
import kombu.messaging
import socket
import ssl
import sys
import time
import uuid

from oslo.config import cfg

from glance.rpc import amqp as rpc_amqp
from glance.utils import networkutils


kombu_opts = [
    cfg.StrOpt('kombu_ssl_version',
        default = '',
        help = 'SSL version to use (valid only if SSL enabled)'),
    cfg.StrOpt('kombu_ssl_keyfile',
        default = '',
        help = 'SSL key file (valid only if SSL enabled)'),
    cfg.StrOpt('kombu_ssl_certfile',
        default = '',
        help = 'SSL cert file (valid only if SSL enabled)'),
    cfg.StrOpt('kombu_ssl_ca_certs',
        default = '',
        help = ('SSL certification authority file '
               '(valid only if SSL enabled)')),
    cfg.StrOpt('rabbit_host',
        default = '127.0.0.1',
        help = 'the RabbitMQ host'),
    cfg.IntOpt('rabbit_port',
        default = 5672,
        help = 'the RabbitMQ port'),
    cfg.ListOpt('rabbit_hosts',
        default = ['$rabbit_host:$rabbit_port'],
        help = 'RabbitMQ HA'),
    cfg.BoolOpt('rabbit_use_ssl',
        default = False,
        help = 'connect over SSL for RabbitMQ'),
    cfg.StrOpt('rabbit_userid',
        default = 'guest',
        help = 'the RabbitMQ userid'),
    cfg.StrOpt('rabbit_password',
        default = 'guest',
         help = 'the RabbitMQ password'),
    cfg.StrOpt('rabbit_virtual_host',
        default = '/',
        help = 'the RabbitMQ virtual host'),
    cfg.IntOpt('rabbit_retry_interval',
        default = 1,
        help = 'how frequently to retry connecting with RabbitMQ'),
    cfg.IntOpt('rabbit_retry_backoff',
        default = 2,
        help = 'how long to backoff for between retries when connecting '
        'to RabbitMQ'),
    cfg.IntOpt('rabbit_max_retries',
        default = 0,
        help = 'maximum retries with trying to connect to RabbitMQ '
       '(the default of 0 implies an infinite retry count)'),
    cfg.BoolOpt('rabbit_durable_queues',
        default = False,
        help = 'use durable queues in RabbitMQ'),
    cfg.BoolOpt('rabbit_ha_queues',
        default = False,
        help = "Use HA queues"),
    ]

CONF = cfg.CONF
CONF.register_opts(kombu_opts)


def _get_queue_arguments(conf):
    return {'x-ha-policy':'all'} if conf.rabbit_ha_queues else{}

class ConsumerBase(object):
    def __init__(self, channel, callback, tag, **kwargs):

        self.callback = callback
        self.tag = str(tag)
        self.kwargs = kwargs
        self.queue = None
        self.reconnect(channel)

    def reconnect(self, channel):
        """
        Re-declare the queue after a rabbit reconnect
        """
        self.channel = channel
        self.kwargs['channel'] = channel
        self.queue = kombu.entity.Queue(**self.kwargs)
        self.queue.declare()

    def consume(self, *args, **kwargs):
        """
        declare the amqp channel,
        """
        print "consume***************", self.queue
        options = {'consumer_tag': self.tag}
        options['nowait'] = kwargs.get('nowait', False)
        callback = kwargs.get('callback', self.callback)

        if not callback:
            raise ValueError("No Callback defined")

        def _callback(raw_message):
            message = self.channel.message_to_python(raw_message)
            try:
                callback(message.payload)
                message.ack()
            except Exception:
                pass
        self.queue.consume(*args, callback = _callback, **options)


class DirectConsumer(ConsumerBase):
    def __init__(self, conf, channel, msg_id, callback, tag, **kwargs):
        """
        Init a direct queue
        """

        options = {
                'durable': False,
                'auto_delete': True,
                'exclusive':True}
        options.update(kwargs)
        exchange = kombu.entity.Exchange(name = msg_id,
                                        type = 'direct',
                                        durable = options['durable'],
                                        auto_delete = options['auto_delete'])
        super(DirectConsumer, self).__init__(channel, callback, tag, name = msg_id, exchange = exchange,
                                            routing_key = msg_id, **options)

class TopicConsumer(ConsumerBase):
    def __init__(self, conf, channel, topic, callback, tag, name = None,
                exchange_name = None, **kwargs):
        options = {'durable': conf.rabbit_durable_queues,
                    'queue_arguments': _get_queue_arguments(conf),
                    'auto_delete': False,
                    'exclusive': False
            }
        options.update(kwargs)
        #TODO
        exchange_name = exchange_name or rpc_amqp.get_control_exchange(conf)
        exchange = kombu.entity.Exchange(name = exchange_name,
                                        type = 'topic',
                                        durable = options['durable'],
                                        auto_delete = options['auto_delete'])
        super(TopicConsumer, self).__init__(channel,
                                        callback,
                                        tag,
                                        name = name or topic,
                                        exchange = exchange,
                                        routing_key = topic,
                                        **options)

class FanoutConsumer(ConsumerBase):
    def __init__(self, conf, channel, topic, callback, tag, **kwargs):
        """
        """
        unique = uuid.uuid4().hex
        exchange_name = "%s_fanout" % topic
        queue_name = '%s_fanout_%s' % (topic, unique)

        options = {'durable': False,
                    'queue_arguments': _get_queue_arguments(conf),
                    'auto_delete':True,
                    'exclusive': True}
        options.update(kwargs)

        exchange = kombu.entity.Exchange(name = exchange_name, type = 'fanout',
                                        durable = options['durable'],
                                        auto_delete = options['auto_delete'])
        super(FanoutConsumer, self).__init__(channel, callback, tag,
                                            name = queue_name, exchange = exchange,
                                            routing_key = topic, **options)

class PublisherBase(object):
    def __init__(self, channel, exchange_name, routing_key, **kwargs):
        """
        """
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.kwargs = kwargs

        self.reconnect(channel)

    def reconnect(self, channel):
        self.exchange = kombu.entity.Exchange(name = self.exchange_name,
                                                **self.kwargs)

        self.producer = kombu.messaging.Producer(exchange = self.exchange,
                                                channel = channel,
                                                routing_key = self.routing_key)


    def send(self, msg):
        """
        Send a messages
        """
        print msg
        self.producer.publish(msg)

class DirectPublisher(PublisherBase):

    def __init__(self, conf, channel, msg_id, **kwargs):
        options = {'durable': False,
                    'auto_delete': True,
                    'exclusive': True}
        options.update(kwargs)
        super(DirectPublisher, self).__init__(channel, msg_id, msg_id,
                                                type = 'direct', **options)

class TopicPublisher(PublisherBase):
    def __init__(self, conf, channel, topic, **kwargs):
        options = {'durable': conf.rabbit_durable_queues,
                    'auto_delete': False,
                    'exclusive': False}
        options.update(kwargs)
        exchange_name = rpc_amqp.get_control_exchange(conf)
        super(TopicPublisher, self).__init__(channel, exchange_name, topic,
                                                type = 'topic', **options)


class FanoutPublisher(PublisherBase):
    def __init__(self, conf, channel, topic, **kwargs):
        """
        """

        options = {'durable': False,
                    'auto_delete': True,
                    'exclusive': True}
        options.update(kwargs)

        super(FanoutPublisher, self).__init__(channel, '%s_fanout' % topic,
                                                None, type = 'fanout', **options)



class NotifyPublisher(TopicPublisher):
    def __init__(self, conf, channel, topic, **kwargs):
        self.durable = kwargs.pop('durable', conf.rabbit_durable_queues)
        self.queue_arguments = _get_queue_arguments(conf)
        super(NotifyPublisher, self).__init__(conf, channel, topic, **kwargs)

    def reconnect(self, channel):
        super(NotifyPublisher, self).__init__(channel)

        queue = kombu.entity.Queue(channel = channel,
                                    exchange = self.exchange,
                                    durable = self.durable,
                                    name = self.routing_key,
                                    routing_key = self.routing_key,
                                    queue_arguments = self.queue_arguments)
        queue.declare()


class Connection(object):
    pool = None

    def __init__(self, conf, server_params = None):
        self.consumers = []
        self.consumer_thread = None
        self.conf = conf
        self.max_retries = self.conf.rabbit_max_retries

        if self.max_retries <= 0:
            self.max_retries = None
        self.interval_start = self.conf.rabbit_retry_interval
        self.interval_stepping = self.conf.rabbit_retry_backoff

        self.interval_max = 30
        self.memory_transport = False

        if server_params is None:
            server_params = {}

        server_params_to_kombu_params = {'username': 'userid'}

        ssl_params = self._fetch_ssl_params()
        params_list = []

        for adr in self.conf.rabbit_hosts:
            hostname, port = networkutils.parse_host_port(
                    adr, default_port = self.conf.rabbit_port)

            params = {
                'hostname': hostname,
                'port': port,
                'userid': self.conf.rabbit_userid,
                'password': self.conf.rabbit_password,
                'virtual_host': self.conf.rabbit_virtual_host, }

            for sp_key, value in server_params.iteritems():
                p_key = server_params_to_kombu_params.params.get(sp_key, sp_key)
                params[p_key] = value

            if self.conf.fake_rabbit:
                params['transport'] = 'memory'
            else:
                params['ssl'] = False
            params_list.append(params)
        self.params_list = params_list
        self.memory_transport = self.conf.fake_rabbit
        self.connection = None
        self.reconnect()

    def _fetch_ssl_params(self):
        ssl_params = dict()

        if self.conf.kombu_ssl_keyfile:
            ssl_params["keyfile"] = self.conf.kombu_ssl_keyfile
        if self.conf.kombu_ssl_certfile:
            ssl_params["certfile"] = self.conf.kombu_ssl_certfile
        if self.conf.kombu_ssl_ca_certs:
            ssl_params['ca_certs'] = self.conf.kombu_ssl_ca_certs
            ssl_params['cert_reqs'] = ssl.CERT_REQUIRED
        if not ssl_params:
            return True

        else:
            return ssl_params


    def _connect(self, params):
        """
        Connect to rabbit
        """
        if self.connection:
            try:
                self.connection.close()
            except self.connection_errors:
                pass
            self.connection = None
        self.connection_errors = None
        #from key value in  params:
        #    print key, value
        self.connection = kombu.connection.BrokerConnection(**params)
        self.connection_errors = self.connection.connection_errors

        if self.memory_transport:
            self.connection.transport.polling_interval = 0.0
        self.consumer_num = itertools.count(1)
        self.connection.connect()

        self.channel = self.connection.channel()

        if self.memory_transport:
            self.channel._new_queue('ae.undeliver')
        for consumer in self.consumers:
            consumer.reconnect(self.channel)

    def reconnect(self):

        attempt = 0

        while 1:
            attempt += 1
            params = self.params_list[attempt % len(self.params_list)]
            try:
                self._connect(params)
                return
            except (IOError, self.connection_errors) as e:
            #except IOError, e:

                pass

            except Exception, e:

                if 'timeout' not in str(e):
                    raise

            if self.max_retries and attempt == self.max:
                sys.exit(1)

            if attempt == 1:
                sleep_time = self.interval_start or 1
            elif attempt > 1:
                sleep_time += self.interval_stepping
            if self.interval_max:
                sleep_time = min(sleep_time, self.interval_max)

            time.sleep(sleep_time)


    def ensure(self, error_callback, method, *args, **kwargs):
        while 1:
            try:
                return method(*args, **kwargs)
            except (self.connection_errors, socket.timeout, IOError), e:
                pass
            except Exception, e:
                if 'timeout' not in str(e):
                    raise
            if error_callback:
                error_callback(e)

            self.reconnect()

    def get_channel(self):
        return self.channel

    def close(self):
        self.cancel_consumer_thread()
        self.connection.release()
        self.connection = None


    def reset(self):
        """
        reset a connection so it can be used again
        """
        self.cancel_consumer_thread()
        self.channel.close()
        self.channel = self.connection.channel()

        if self.memory_transport:
            self.channel._new_queue('ae.undeliver')
        self.consumers = []


    def declare_consumer(self, consumer_cls, topic, callback):
        """
        Create a Consumer using the class that was passed in and add it to our list of consumers
        """

        def _connect_error(exc):
            pass

        def _declare_consumer():
            consumer = consumer_cls(self.conf, self.channel, topic, callback,
                                    self.consumer_num.next())
            self.consumers.append(consumer)
            return consumer

        return self.ensure(_connect_error, _declare_consumer)

    def iterconsume(self, limit = None, timeout = None):
        info = {'do_consume': True}

        def _error_callback(exc):
            if isinstance(exc, socket.timeout):
                pass
                #raise rpc_common.Timeout()
            else:
                info['do_consume'] = True

        def  _consume():
            if info["do_consume"]:
                queues_head = self.consumers[:-1]
                queues_tail = self.consumers[-1]
                for queue in queues_head:
                    queue.consume(nowait = True)
                queues_tail.consume(nowait = False)
                info['do_consume'] = False
            return self.connection.drain_events(timeout = timeout)

        for iteration in itertools.count(0):
            if limit and iteration >= limit:
                raise StopIteration
            yield self.ensure(_error_callback, _consume)

    def cancel_consumer_thread(self):
        """
        """
        if self.consumer_thread is not None:
            self.consumer_thread.kill()
            try:
                self.consumer_thread.wait()
            except greenlet.GreenletExit:
                pass
            self.consumer_thread = None

    def publisher_send(self, cls, topic, msg, **kwargs):
        """
        Send to a publisher based on the publisher class
        """
        def _error_callback(exc):
            log_info = {'topic': topic, 'err_str': str(exc)}

        def _publish():
            publisher = cls(self.conf, self.channel, topic, **kwargs)
            publisher.send(msg)

        self.ensure(_error_callback, _publish)


    def declare_direct_consumer(self, topic, callback = None,
                                 queue_name = None):
        self.declare_consumer(DirectConsumer, topic, callback)


    def declare_topic_consumer(self, topic, callback = None,
                                    queue_name = None):
        self.declare_consumer(functools.partial(TopicConsumer,
                            name = queue_name,),
                             topic, callback)
    def declare_fanout_consumer(self, topic, callback):
        self.declare_consumer(FanoutConsumer, topic, callback)

    def direct_send(self, msg_id, msg):
        self.publisher_send(DirectPublisher, msg_id, msg)


    def topic_send(self, topic, msg):
        self.publisher_send(TopicPublisher, topic, msg)

    def fanout_send(self, topic, msg):
        self.publisher_send(FanoutPublisher, topic, msg)

    def notify_send(self, topic, msg, **kwargs):
        self.publisher_send(NotifyPublisher, topic, msg, **kwargs)

    def consume(self, limit = None):
        """
        Consume from all queues/Consumers
        """

        it = self.iterconsume(limit = limit)
        print "enter consume", it
        while 1:
            try:
                it.next()
            except StopIteration:
                return

    def consume_in_thread(self):
        def _consumer_thread():
            try:
                self.consume()
            except greenlet.GreenletExit:
                return

        if self.consumer_thread is None:
            self.consumer_thread = eventlet.spawn(_consumer_thread)

        return self.consumer_thread

    def create_consumer(self, topic, proxy, fanout = False):
        proxy_cb = rpc_amqp.ProxyCallback(
                    self.conf, proxy,
                    rpc_amqp.get_connection_pool(self.pool, Connection))
        if fanout:
            self.declare_fanout_consumer(topic, proxy_cb)
        else:
            self.declare_topic_consumer(topic, proxy_cb)

    def create_worker(self, topic, proxy, pool_name):
        """
        """
        proxy_cb = rpc_amqp.ProxyCallback(
                    self.conf, proxy,
                    rpc_amqp.get_connection_pool(self.conf, Connection))
        self.declare_topic_consumer(topic, proxy_cb, pool_name)


def create_connection(conf, new = True):
    """
    """
    return rpc_amqp.create_connection(conf, new,
                rpc_amqp.get_connection_pool(conf, Connection))

def multicall(conf, topic, msg, timeout = None):
    return rpc_amqp.multicall(conf, topic, msg, timeout,
                    rpc_amqp.get_connection_pool(conf, Connection))

def call(conf, topic, msg, timeout = None):
    """
    """
    return rpc_amqp.call(conf, topic, msg, timeout,
                    rpc_amqp.get_connection_pool(conf, Connection))

def cast(conf, topic, msg):
    """
    """
    return rpc_amqp.cast(conf, topic, msg,
                    rpc_amqp.get_connection_pool(conf, Connection))

def fanout_cast(conf, topic, msg):
    """
    """
    return rpc_amqp.fanout_cast(conf, topic, msg,
                     rpc_amqp.get_connection_pool(conf, Connection))

def cast_to_server(conf, server_params, topic, msg):
    """
    """
    return rpc_amqp.cast_to_server(conf, server_params, topic, msg,
                                rpc_amqp.get_connection_pool(conf, Connection))

def fanout_cast_to_server(conf, server_params, topic, msg):
    """
    """
    return rpc_amqp.fanout_cast_to_server(conf, server_params, topic, msg,
                                    rpc_amqp.get_connection_pool(conf, Connection()))

def notify(conf, topic, msg):
    """
    """
    return rpc_amqp.notify(conf, topic, msg,
                            rpc_amqp.get_connection_pool(conf, Connection))

def cleanup():
    return rpc_amqp.cleanup(Connection.pool)
