#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import os
import socket

from oslo.config import cfg
import webob.dec
import webob
import webob.exc
from paste import deploy
import eventlet
import eventlet.wsgi
import greenlet
import ssl
import routes.middleware

wsgi_opts = [
    cfg.StrOpt('api_paste_config',
               default='glance-api-paste.ini',
               help='File name for the paste.deploy config for glance-api'),
    
    ]

CONF = cfg.CONF
CONF.register_opts(wsgi_opts)



class Server(object):
    
    default_pool_size=1000
    
    def __init__(self, name, app, host='0.0.0.0',
                 port=0, pool_size=None,
                 protocol=eventlet.wsgi.HttpProtocol, backlog=128,
                 use_ssl=False, max_url_len=None):
        self.name = name
        self.app = app
        self._server = None
        self._protocol=protocol
        self._pool = eventlet.GreenPool(pool_size or self.default_pool_size)
        self._use_ssl = use_ssl
        self._max_url_len = max_url_len
        
        if backlog < 1:
            raise
        bind_addr = (host, port)
        try:
            info = socket.getaddrinfo(bind_addr[0], bind_addr[1],
                                      socket.AF_UNSPEC,
                                      socket.SOCK_STREAM)[0]
            family = info[0]
            bind_addr = info[-1]
        except Exception:
            famiy = socket.AF_INET
        self._socket = eventlet.listen(bind_addr, family, backlog=backlog)
        (self.host, self.port) = self._socket.getsockname()[0:2]
        
    def start(self):
        if self._use_ssl:
            try:
                ca_file = CONF.ssl_ca_file
                cert_file = CONF.ssl_cert_file
                key_file = CONF.ssl_key_file
                if cert_file and not os.path.exists(cert_file):
                    raise
                if ca_file and not os.path.exists(ca_file):
                    raise
                if key_file and not os.path.exists(key_file):
                    raise
                if self._use_ssl and (not cert_file or not key_file):
                    raise
                ssl_kwargs = {
                    'server_side': True,
                    'certfile': cert_file,
                    'keyfile': key_file,
                    'cert_reqs': ssl.CERT_NONE}
                if CONF.ssl_ca_file:
                    ssl_kwargs['ca_certs'] = ca_file
                    ssl_kwargs['cert_reqs'] = ssl.CERT_REQUIRED
                self._socket = eventlet.wrap_ssl(self.socket, **ssl_kwargs)
                self._socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, 1)
                self._socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_KEEPALIVE, 1)
                if hasattr(socket, 'TCP_KEEPIDLE'):
                    self._socket.setsockopt(socket.IPPROTO_TCP,
                                            socket.TCP_KEEPIDLE,
                                            CONF.tcp_keepidle)
            except Exception:
                raise
        
        wsgi_kwargs = {
            'func': eventlet.wsgi.server,
            'sock': self._socket,
            'site': self.app,
            'protocol': self._protocol,
            'custom_pool': self._pool
            }
        if self._max_url_len:
            wsgi_kwargs['url_length_limit'] = self._max_url_len
        self._server = eventlet.spawn(**wsgi_kwargs)
    
    def stop(self):
        if self._server is not None:
            self._pool.resize(0)
            self._server.kill()
    
    def wait(self):
        try:
            self._server.wait()
        except greenlet.GreenletExit:
            raise
        

class Request(webob.Request):   
    pass


class Application(object):
    '''
    WSGI base class, in subclass need to implement __call__
    '''
    
    @classmethod
    def factory(cls, global_config, **local_config):
        '''
        
        :param cls:
        :param global_config:
        '''
        return cls(**local_config)
    
    def __call__(self, environ, start_response):
        '''
        need to implement in subclass
        :param environ:
        :param start_response:
        '''
        raise NotImplementedError("you must implement __call__")


class Middleware(Application):
    '''
    Base WSGI middleware
    '''
    
    @classmethod
    def factory(cls, global_config, **local_config):
        def _factory(app):
            return cls(app, **local_config)
        return _factory

    def __init__(self, application):
        self.application = application
    
    def process_request(self, req):
        return None
    
    def process_response(self, response):
        return response
    
    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        response = self.process_request(req)
        if response:
            return response
        response =  req.get_response(self.application)
        return self.process_response(response)


class Router(object):
    
    def __init__(self, mapper):
        self.map = mapper
        print self.map
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          self.map)
        
    @webob.dec.wsgify(RequestClass = Request)
    def __call__(self, req):
        return self._router
    
    @staticmethod
    @webob.dec.wsgify(RequestClass = Request)
    def _dispatch(req):
        print "enter router call", req.environ.keys(), req.environ
        match = req.environ['wsgiorg.routing_args'][1]
        if not match:
            return webob.exc.HTTPNotFound()
        app = match['controller']
        return app


class Loader(object):
    
    def __init__(self, config_path=None):
        '''
        
        :param config_path:
        '''
        config_path = config_path or CONF.api_paste_config
        if os.path.exists(config_path):
            self.config_path = config_path
        else:
            self.config_path = CONF.find_file(config_path)
            
        if not self.config_path:
            pass
    
    def load_app(self, name): 
        '''
        
        :param name:
        '''
        try:
            return deploy.loadapp("config:%s" % self.config_path, name=name)
        except LookupError as err:
            pass
        
