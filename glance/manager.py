#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import time

import eventlet
from oslo.config import cfg

from glance.rpc import dispatcher as rpc_dispatcher

periodic_opts = [
    cfg.BoolOpt('run_external_periodic_tasks',
                default=True,
                help='Some periodic tasks can be run in a separate process')             
    ]
CONF = cfg.CONF
CONF.register_opts(periodic_opts)
CONF.import_opt('my_ip', 'glance.utils.addressconf')
DEFAULT_INTERVAL=60.0

def periodic_task(*args, **kwargs):
    def decorator(f):
        if 'ticks_between_runs' in kwargs:
            raise
        f._periodic_task = True
        f._periodic_external_ok = kwargs.pop('external_process_ok', False)
        if f._periodic_external_ok and not CONF.run_external_periodic_tasks:
            f._periodic_enabled = False
        else:
            f._periodic_enabled = kwargs.pop('enabled', True)
        f._periodic_spacing = kwargs.pop('enabled', True)
        if kwargs.pop('run_immediately', False):
            f._periodic_last_run = None
        else:
            f._periodic_last_run = time.time()
        return f
    if kwargs:
        return decorator
    else:
        return decorator(args[0])

class ManagerMeta(type):
    def __init__(cls, names, bases, dict_):
        super(ManagerMeta, cls).__init__(names, bases, dict_)
        try:
            cls._periodic_tasks = cls._periodic_tasks[:]
        except AttributeError:
            cls._periodic_tasks = []
        try:
            cls._periodic_last_run = cls._periodic_last_run.copy()
        except AttributeError:
            cls._periodic_last_run = {}
        try:
            cls._periodic_spacing = cls._periodic_spacing.copy()
        except AttributeError:
            cls._periodic_spacing = {}
        
        for value in cls.__dict__.values():
            if getattr(value, '_periodic_task', False):
                task = value
                name = task.__name__
                if task._periodic_spacing < 0:
                    continue
                if not task._periodic_enabled:
                    continue
                if task._periodic_spacing == 0:
                    task._periodic_spacing = None
                cls._periodic_tasks.append((name, task))
                cls._periodic_spacing[name] = task._periodic_spacing
                cls._periodic_last_run[name] = task._periodic_last_run

class Manager(object):
    __metaclass__ = ManagerMeta
    
    def __init__(self, host=None):
        if not host:
            host = CONF.my_ip
        self.host = host
        self.backdoor_port = None
        
    def create_rpc_dispatcher(self):
        return rpc_dispatcher.RpcDispatcher([self])

    def periodic_tasks(self, raise_on_error=False):
        idle_for = DEFAULT_INTERVAL
        for task_name, task in self._periodic_tasks:
            full_task_name = ''.join([self.__class__.__name__, task_name])
            if self._periodic_spacing[task_name] is None:
                wait = 0
            elif self._periodic_last_run[task_name] is None:
                wait = 0
            else:
                due = (self._periodic_last_run[task_name] + 
                       self._periodic_spacing[task_name])
                wait = max(0, due - time.time())
                if wait> 0.2:
                    if wait < idle_for:
                        idle_for = wait
                    continue
                self._periodic_last_run[task_name] = time.time()
                try:
                    task(self)
                except Exception as e:
                    raise
                
                if (not self._periodic_spacing[task_name] is None and
                    self._periodic_spacing[task_name] < idle_for):
                    idle_for = self._periodic_spacing[task_name]
                eventlet.sleep(0)
        return idle_for
        
    def init_host(self, **kwargs):
        pass
        
    def post_start_hook(self, **kwargs):
        pass
        
    def pre_start_hook(self, **kwargs):
        pass


                

            
