#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import webob.exc
import webob.dec
import routes

from glance import wsgi as base_wsgi


class APIMapper(routes.Mapper):
    
    def routematch(self, url=None, environ=None):
        if url == "":
            result = self._match("", environ)
            return result[0], result[1]
        return routes.Mapper.routematch(self, url, environ)
    
    def connect(self, *args, **kwargs):
        kwargs.setdefault('requirements', {})
        if not kwargs['requirements'].get('format'):
            kwargs['requirements']['format'] = 'json|xml'
        return routes.Mapper.connect(self, *args, **kwargs)


class ProjectMapper(APIMapper):
    def resource(self, member_name, collection_name, **kwargs):
        if 'parent_resource' not in kwargs:
            kwargs['path_prefix'] = None
        else:
            parent_resource = kwargs['parent_resource']
            p_collection = parent_resource['collection_name']
            p_member = parent_resource['member_name']
            kwargs['path_prefix'] = '%s/:%s_id' %(p_collection,
                                                                p_member)
        routes.Mapper.resource(self, member_name, collection_name,
                               **kwargs)


class APIRouter(base_wsgi.Router):
    
    @classmethod
    def factory(cls, global_config, **local_config):
        return cls()
    
    def __init__(self, init_only=None):
        mapper = ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper, init_only)
        super(APIRouter, self).__init__(mapper)
    
    def setup_routes(self, mapper, init_only):
        raise NotImplementedError()
