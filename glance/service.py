#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import sys
import os
import inspect
import random
import signal
import time
import errno

from oslo.config import cfg
import eventlet
import greenlet

from glance import wsgi
from glance.utils import importutils
from glance.utils import eventlet_backdoor
from glance.utils import loopingcall
from glance import rpc


CONF = cfg.CONF

service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='seconds between nodes reporting state to datastore'),
    cfg.IntOpt('periodic_interval',
               default=60,
               help=""),
    cfg.BoolOpt('periodic_enable',
                default=True,
                help='enable periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help=""),
    cfg.StrOpt('glance_listent_host',
               default="0.0.0.0",
               help='Ip address for glance'),
    cfg.IntOpt('glance_listen_port',
               default=5555,
               help="glance service listen port"),
    cfg.IntOpt('periodic_interval_max',
               default=60,
               help='between periodic execute time'),
    cfg.IntOpt("service_down_time",
               default=60,
               help="maximum time since last check-in for up service"),
    cfg.BoolOpt("enabled_ssl_apis",
                default=False,
                help="should use "),
    cfg.IntOpt("glance_workers",
               default=None,
               help="Number of workers for glance API service"),
    cfg.StrOpt('glance_agent_manager',
                default="glance.glance_agent.manager.GlanceAgentManager",
                help=''),
    cfg.StrOpt('glance_push_manager',
                default="glance.glance_push.manager.GlancePushManager",
                help=''),
    cfg.StrOpt('glance_pull_manager',
                default="glance.glance_pull.manager.GlancePullManager",
                help=''),
        ]

CONF.register_opts(service_opts)
CONF.import_opt('my_ip', 'glance.utils.addressconf')


class SignalExit(SystemExit):
    
    def __init__(self, signo, excode=1):
        super(SignalExit, self).__init__(excode)
        self.signo = signo


class Launcher(object):
    
    def __init__(self):
        self._services = []
        self.backdoor_port = eventlet_backdoor.initialize_if_enabled()
    
    @staticmethod
    def run_server(server):
        server.start()
        server.wait()
    
    def launch_server(self, server):
        if self.backdoor_port is not None:
            server.backdoor_port = self.backdoor_port
        gt = eventlet.spawn(self.run_server, server)
        self._services.append(gt)
    
    def stop(self):
        for service in self._services:
            service.kill()
    
    def wait(self):
        for service in self._services:
            try:
                service.wait()
            except greenlet.GreenletExit:
                pass


class ServiceLauncher(Launcher):
    
    def _handle_signal(self, signo, frame):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        raise SignalExit(signo)
    
    def wait(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        status=None
        try:
            super(ServiceLauncher, self).wait()
        except SignalExit as exc:
            status = exc.code
        finally:
            self.stop()
        if status is not None:
            sys.exit(status)

        
class ServerWrapper(object):
    def __init__(self, server, workers):
        self.server = server
        self.workers = workers
        self.children = set()
        self.forktimes = []


class ProcessLauncher(object):
    
    def __init__(self):
        self.children = {}
        self.sigcaught = None
        self.running = True
        rfd, self.writepipe = os.pipe()
        self.readpipe = eventlet.greenio.GreenPipe(rfd, 'f')
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
    
    def _handle_signal(self, signo, frame):
        self.sigcaught = signo
        self.running = False
        
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    def _pipe_watcher(self):
        self.readpipe.read()
        sys.exit(1)
    
    def _child_process(self, server):
        def _sigterm(*args):
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            raise SignalExit(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _sigterm)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        eventlet.hubs.use_hub()
        os.close(self.writepipe)
        eventlet.spawn(self._pipe_watcher)
        random.seed()
        launcher = Launcher()
        launcher.run_server(server)
    
    def _start_child(self, wrap):
        if len(wrap.forktimes) > wrap.workers:
            if time.time() - wrap.forktimes[0] < wrap.workers:
                time.sleep(1)
            wrap.forktimes.pop(0)
        wrap.forktimes.append(time.time())
        pid = os.fork()
        if pid == 0:
            status = 0
            try:
                self._child_process(wrap.server)
            except SignalExit as exc:
                signame = {signal.SIGTERM: 'SIGTERM',
                           signal.SIGINT: 'SIGINT'}[exc.signo]
                status = exc.code
            except SystemExit as exc:
                status = exc.code
            except BaseException as exc:
                status = 2
            finally:
                wrap.server.stop()
            os._exit(status)
            
        wrap.children.add(pid)
        self.children[pid] = wrap
        return pid
    
    def launch_server(self, server, workers=1):
        wrap = ServerWrapper(server, workers)
        while self.running and len(wrap.children) < wrap.workers:
            self._start_child(wrap)
    
    def _wait_child(self):
        try:
            pid, status = os.wait()
        except OSError as exc:
            return None
        
        if os.WIFSIGNALED(status):
            sig = os.WTERMSIG(status)
        else:
            code = os.WEXITSTATUS(status)
        
        if pid not in self.children:
            return None
        wrap = self.children.pop(pid)
        wrap.children.remove(pid)
        return wrap
    
    def wait(self):
        while self.running:
            wrap = self._wait_child()
            if not wrap:
                continue
            while self.running and len(wrap.children) < wrap.workers:
                self._start_child(wrap)
        if self.sigcaught:
            signame = {signal.SIGTERM: 'SIGTERM',
                       signal.SIGINT: 'SIGINT'}[self.sigcaught]
        for pid in self.children:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError as exc:
                if exc.errno != errno.ESRCH:
                    raise
        
        if self.children:
            while self.children:
                self._wait_child()


class Service(object):
    
    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, *args, **kwargs):
        
        self.host = host
        self.binary = binary
        self.topic = topic
        self.manager_class_name = manager
        
        manager_class = importutils.import_class(self.manager_class_name)
        self.manager = manager_class(host=self.host, *args, **kwargs)
        self.report_interval = report_interval
        self.periodic_enable = periodic_enable
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.periodic_interval_max = periodic_interval_max
        self.saved_args, self.saved_kwargs = args, kwargs
        self.timers = []
        self.backdoor_port = None
    
    def start(self):
        #self.basic_config_check()
        self.manager.init_host()
        print dir(self.manager)
        self.model_disconnected = False
        if self.backdoor_port:
            self.manager.backdoor_port = self.backdoor_port
        self.conn = rpc.create_connection(new=True) 
        self.manager.pre_start_hook(rpc_connection=self.conn)
        rpc_dispatcher = self.manager.create_rpc_dispatcher()
        self.conn.create_consumer(self.topic, rpc_dispatcher, fanout=False)
        node_topic = '%s.%s' %(self.topic, self.host)
        print node_topic
        self.conn.create_consumer(node_topic, rpc_dispatcher, fanout=False)
        self.conn.create_consumer(self.topic, rpc_dispatcher, fanout=True)
        print "3 consumers have been created!"
        self.conn.consume_in_thread()
        #if self.report_interval:
        #    pulse = loopingcall.LoopingCall(self.report_state)
        #    pulse.start(interval=self.report_interval,
        #                initial_delay=self.report_interval)
        #    self.timers.append(pulse)
        if self.periodic_enable:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None
            periodic = loopingcall.LoopingCall(self.periodic_tasks)
            print self.periodic_interval_max, initial_delay, '--' * 10
            periodic.start(interval=self.periodic_interval_max,
                           initial_delay=initial_delay)
            self.timers.append(periodic)
        self.manager.post_start_hook()
    
    @classmethod
    def create(cls, host=None, binary=None, topic=None, manager=None,
               report_interval=None, periodic_enable=None,
               periodic_fuzzy_delay=None, periodic_interval_max=None):
        
        if not host:
            host = CONF.my_ip
        if not binary:
            binary = os.path.basename(inspect.stack())[-1][1]
        if not topic:
            topic = binary.rpartition('glance-')[2]
        if not manager:
            manager_cls = ('%s_manager' % binary.rpartition('glance-')[2])
            manager = CONF.get(manager_cls, None)
        if report_interval is None:
            report_interval = CONF.report_interval
        if periodic_enable is None:
            periodic_enable = CONF.periodic_enable
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = CONF.periodic_fuzzy_delay
        if periodic_interval_max is None:
            periodic_interval_max = CONF>periodic_interval_max
        service_obj =  cls(host, binary, topic, manager,
                           report_interval=report_interval,
                           periodic_enable=periodic_enable,
                           periodic_fuzzy_delay=periodic_fuzzy_delay,
                           periodic_interval_max=periodic_interval_max)
        return service_obj
    
    def kill(self):
        self.stop()
        
    def stop(self):
        self.conn.close()
        
        for x in self.timers:
            x.stop()
        self.timers = []
    
    def wait(self):
        for x in self.timers:
            x.wait()
        
    def periodic_tasks(self):
        return self.manager.periodic_tasks()
        
        

class WSGIService(object):
    
    def __init__(self, name, loader=None, use_ssl=False, max_url_len=None):
        '''
        
        :param name:
        :param loader:
        :param use_ssl:
        :param max_url_len:
        '''
        self.name = name
        self.manager = self._get_manager()
        self.loader = loader or wsgi.Loader() 
        self.app = self.loader.load_app(name)
        self.host = getattr(CONF, "%s_listen" % name, CONF.my_ip)
        self.port = getattr(CONF, "%s_listen_port" % name, 0)
        self.workers = getattr(CONF,  "%s_workers" % name, None)
        self.use_ssl = use_ssl
        self.server = wsgi.Server(name, self.app,
                                  host=self.host,
                                  port=self.port,
                                  use_ssl=self.use_ssl,
                                  max_url_len=max_url_len)
        self.port = self.server.port
        self.backdoor_port = None
    
    def _get_manager(self):
        f1 = "%s_manager" % self.name
        if f1 not in CONF:
            return None
        manager_class_name = CONF.get(f1, None)
        if not manager_class_name:
            return None
        manager_class = importutils.import_class(manager_class_name)
        return manager_class
    
    def start(self):
        if self.manager:
            self.manager.init_host()
            self.manager.pre_start_hook()
        if self.backdoor_port:
            self.manager.backdoor_port = self.backdoor_port
        self.server.start()
        if self.manager:
            self.manager.post_start_hook()
    
    def stop(self): 
        self.server.stop
    
    def wait(self):
        self.server.wait()


_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise
    if workers:
        _launcher = ProcessLauncher()
        _launcher.launch_server(server, workers)
    else:
        _launcher = ServiceLauncher()
        _launcher.launch_server(server)


def wait():
    _launcher.wait()
