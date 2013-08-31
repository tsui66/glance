#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

from glance.api.glance_api import wsgi

class Controller(wsgi.Controller):
    
    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
    
    def index(self, req):
        print "enter index"
        return "eeee"
    
    def detail(self, req):
        print "enter detail"
        print req
        return "detail method"
    
    def create(self, req, body):
        print "enter create"
        return {"images": "create method"}
    
    def show(self, req, id, body):
        print "enter show "
        print req
        print id
        print body["php"]
        return  "show method"

    def edit(self, req, id):
        print 'enter edit'
        print req
        print id
        str = "edit method,id:"+id
        return str

    def update(self, req, id):
        print "enter update"
        print req
        print id
        return "update method,and id is ",id
    
def create_resource():
    return wsgi.Resource(Controller())
