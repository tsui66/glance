#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import webob.dec
import webob.exc
 
from glance.api.glance_api import wsgi
from glance import wsgi as base_wsgi
from glance.utils import common

class FaultWrapper(base_wsgi.Middleware):
    
    _status_to_type = {}
    
    @staticmethod
    def status_to_type(status):
        if not FaultWrapper._status_to_type:
            for clazz in common.walk_class_hierarchy(webob.exc.HTTPError):
                FaultWrapper._status_to_type[clazz.code] = clazz
        return FaultWrapper._status_to_type.get(status, 
                                    webob.exc.HTTPInternalServerError)()
    
    def _error(self, inner, req):
        safe = getattr(inner, 'safe', False)
        headers = getattr(inner, 'headers', None)
        status = getattr(inner, 'code', 500)
        if status is None:
            status = 500
        msg_dict = dict(url=req.url, status=status)
        outer = self.status_to_type(status)
        if headers:
            outer.headers = headers
        if safe:
            outer.explanation = '%s: %s' (inner.__class__.__name__,
                                          unicode(inner))
        return wsgi.Fault(outer)
    
    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        try:
            return req.get_response(self.application)
        except Exception as ex:
            print ex
            return self._error(ex, req)
    
