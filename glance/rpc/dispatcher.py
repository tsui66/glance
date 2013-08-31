#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


class RpcDispatcher(object):
    def __init__(self, callbacks):
        self.callbacks = callbacks
        print "enter RpcDispatcher", self.callbacks
        super(RpcDispatcher, self).__init__()
    
    def dispatch(self, method, **kwargs):
        
        for proxyobj in self.callbacks:
            if not hasattr(proxyobj, method):
                continue

            return getattr(proxyobj, method)(**kwargs)
