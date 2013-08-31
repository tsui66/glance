#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


from oslo.config import cfg
import webob.exc
import webob.dec

from glance import wsgi


max_request_body_size_opt = cfg.IntOpt('glance_max_request_body_size',
                                       default = 114688,
                                       help='the maximum body size')

CONF = cfg.CONF
CONF.register_opt(max_request_body_size_opt)


class LimitingReader(object):
    '''
    Reader to limit the size of an incoming request.
    '''
    def __init__(self, data, limit):
        '''
        :param data:
        :param limit:
        '''
        self.data = data
        self.limit = limit
        self.bytes_read = 0
    
    def __iter__(self):
        for chunk in self.data:
            self.bytes_read += len(chunk)
            if self.bytes_read > self.limit:
                msg = "Request is too large"
                raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg)
            else:
                yield chunk
    
    def read(self, i=None):
        result = self.data.read(i)
        self.bytes_read += len(result)
        if self.bytes_read > self.limit:
            msg = "Request is too large"
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg)
        return result


class RequestBodySizeLimiter(wsgi.Middleware):
    
    def __init__(self, *args, **kwargs):
        super(RequestBodySizeLimiter, self).__init__(*args, **kwargs)
    
    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        if req.content_length > CONF.glance_max_request_body_size:
            msg = "Request is too large"
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg)
        if req.content_length is None and req.is_body_readable:
            limiter = LimitingReader(req.body_file,
                                     CONF.glance_max_request_body_size)
            req.body_file = limiter
        return self.application
        
            
