#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-27
#Copyright 2013 nuoqingyun xuqifeng

from glance.api.glance_api import wsgi
from glance.glance_pull.api import GlancePullAPI

class Controller(wsgi.Controller):
    
    def __init__(self, **kwargs):
        self.glance_api = GlancePullAPI()
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

    @wsgi.action("getsysteminfo")
    def get_system_action(self, req, id, body):
        charts = body['getsysteminfo'].get('charts', None)
        date_to = body['getsysteminfo'].get('date_to', None)
        date_from = body['getsysteminfo'].get('date_from', None)
        server = body['getsysteminfo'].get('server', None)
        print charts, date_to, date_from, server
        return self.glance_api.getSystem(charts = charts, 
                    date_to = date_to, 
                    date_from = date_from, 
                    server = server)
            
    @wsgi.action('getserverinfo')
    def get_server_action(self, req, id, body):
        if body:
            filter = body['getserverinfo'].get('filter', None)
            server = body['getserverinfo'].get('server', None)
            return self.glance_api.getServer(filter = filter, 
                    server = server)

    @wsgi.action('gettrafficinfo')
    def get_traffic_action(self, req, id, body):
        if body:
            date = body['gettrafficinfo'].get('date', None)
            domain = body['gettrafficinfo'].get('domain', None)
            traffic =  self.glance_api.getTraffic(date = date,
                    domain = domain)
            return {"traffic": traffic}

    @wsgi.action('portscaninfo')
    def portscan_action(self, req, id, body):
        if body:
            #key = body['portscaninfo'].get('key', None)
            server = body['portscaninfo']
            portscan =  self.glance_api.getPortScan(server = server)
            return {"portscan": portscan}

    @wsgi.action('getprocessinfo')
    def get_process_action(self, req, id, body):
        if body:
            server = body['getprocessinfo'].get('server', None)
            date_to =  body['getprocessinfo'].get('date_to', None)
            process =  self.glance_api.getProcess(server = server,
                                                date_to = date_to)
            return process

def create_resource():
    return wsgi.Resource(Controller())
