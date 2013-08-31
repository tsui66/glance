#!/usr/bin/env python
#encode=utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-5-8
# Copyright 2013 nuoqingyun changchunhe
import json

import webob.exc
import webob.dec
from oslo.config import cfg

from glance import wsgi
from glance import exception

auth_opts=[cfg.BoolOpt('use_forwarded_for', default=False),
           ]

CONF = cfg.CONF
CONF.register_opts(auth_opts)


def pipeline_factory(loader, global_conf, **local_conf):
    '''
    
    :param loader:
    :param global_conf:
    '''
    pipeline = local_conf["glance"]
    pipeline = pipeline.split()
    filters = [loader.get_filter(n) for n in pipeline[:-1]]
    app = loader.get_app(pipeline[-1])
    filters.reverse()
    for filter in filters:
        app = filter(app)
    return app

class AuthContext(wsgi.Middleware):
    
    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        try:
            
            user_id = req.headers.get('X_USER')
        except Exception as e:
            print e
        user_id = req.headers.get('X_USER_ID', user_id)
        if user_id is None:
            return webob.exc.HTTPUnauthorized()
        user_name = req.headers.get('X_USER_NAME')
        auth_token = req.headers.get('X_AUTH_TOKEN',
                        req.headers.get('X_STORAGE_TOKEN'))
        remote_address = req.remote_addr
        context = {}
        context['user_id'] = user_id
        context['user_name'] = user_name
        context['auth_token'] = auth_token
          
        if CONF.use_forwarded_for:
            remote_address = req.headers.get('X-Forwarded-For', remote_address)
        context['remote_address'] = remote_address
        
        req.environ['glance.context'] = context
        print "Auth Context"
        return self.application
        
        
        
        
        
        
