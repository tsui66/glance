#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import eventlet
eventlet.monkey_patch(os=False)

import os
import sys


from oslo.config import cfg
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
                    sys.argv[0]), os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "glance", "__init__.py")):
    sys.path.insert(0, possible_topdir)

from glance import service
from glance.utils import config
from glance import log as logging

api_opts=[
    cfg.StrOpt('api_name',
               default="glance",
               help="glance name")
         ]

CONF = cfg.CONF
CONF.register_opts(api_opts)
CONF.import_opt("enabled_ssl_apis", 'glance.service')


if __name__ == "__main__":
    config.parse_args(sys.argv)
    logging.setup("glance")
    launcher=service.ProcessLauncher()
    should_use_ssl = CONF.enabled_ssl_apis
    
    server = service.WSGIService(CONF.api_name, use_ssl=should_use_ssl,
                                 max_url_len=16384) 
    launcher.launch_server(server, workers=server.workers or 1)
    launcher.wait()
