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


CONF = cfg.CONF
glance_push_manager_opts = [
        cfg.StrOpt('glance_push_topic',
                    default = 'glance_push',
                    help = 'The topic glance push nodes listen on'),
]

CONF.register_opts(glance_push_manager_opts)

from glance import service
from glance import config


if __name__ == "__main__":
    sys.path
    config.parse_args(sys.argv)
    server = service.Service.create(binary='glance_push', topic = CONF.glance_push_topic)
    service.serve(server)
    service.wait()
