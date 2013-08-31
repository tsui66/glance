#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


from oslo.config import cfg

import glance.api
import glance.api.glance_api.glance_pull

class APIRouter(glance.api.APIRouter):
    
    def _setup_routes(self, mapper, init_only):

            
        if init_only is None or 'glance_pull' in init_only:
            self.resources['glance_pull'] = glance.api.glance_api.\
                    glance_pull.create_resource()
            mapper.resource("glance", "glance",
                            controller = self.resources['glance_pull'],
                            collection={"detail":"GET"},
                            member={"action":"POST"})

