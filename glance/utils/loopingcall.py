#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import sys

from eventlet import event
from eventlet import greenthread


class LoopingCall(object):
    
    def __init__(self, f=None, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.f = f
        self._running = False
    
    def start(self, interval, initial_delay):
        self._running = True
        done = event.Event()
        
        def _inner():
            if initial_delay:
                greenthread.sleep(initial_delay)
                
            try:
                while self._running:
                    idle = self.f(*self.args, **self.kwargs)
                    if not self._running:
                        break
                    if  interval:
                        idle=min(idle, interval)
                    greenthread.sleep(idle)
            except Exception:
                done.send_exception(*sys.exc_info())
                return
            else:
                done.send(True)
        self.done = done
        greenthread.spawn(_inner)
        return self.done

    def wait(self):
        return self.done.wait()

    def stop(self):
        self._running = False
