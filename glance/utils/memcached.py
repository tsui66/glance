#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import datetime
import calendar
import time

from oslo.config import cfg


memcache_opts = [
    cfg.ListOpt('memcached_servers',
            default=['127.0.0.1:11211'],
            help='Memcached servers or None for in process cache.'),
    ]
CONF = cfg.CONF
CONF.register_opts(memcache_opts)

def get_client(memcached_servers=None):
    client_cls = Client
    
    if not memcached_servers:
        memcached_servers = CONF.memcached_servers
    if memcached_servers:
        try:
            import memcache
            client_cls = memcache.Client
        except ImportError:
            pass
    return client_cls(memcached_servers, debug=0)

class Client(object):
    def __init__(self, *args, **kwargs):
        self.cache = {}
    
    def get(self, key):
        now = time.time()
        for k in self.cache.keys():
            (timeout, _value) = self.cache[k]
            if timeout and now >= timeout:
                del self.cache[k]
        return self.cache.get(key, (0, None))[1]
    
    def set(self, key, value, time=0, min_compress_len=0):
        timeout = 0
        if time != 0:
            timeout = calendar.timegm((datetime.datetime.utcnow()).timetuple()) + time
        self.cache[key] = (timeout, value)
        return True
    
    def add(self, key, value, time=0, min_compress_len=0):
        if self.get(key) is not None:
            return False
        return self.set(key, value, time, min_compress_len)
    
    def incr(self, key, delta=1):
        value = self.get(key)
        if value is None:
            return None
        new_value = int(value) + delta
        self.cache[key] = (self.cache[key][0], str(new_value))
        return new_value
    
    def delete(self, key, time=0):
        if key in self.cache:
            del self.cache[key]
    
        
            
