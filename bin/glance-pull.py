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
glance_pull_manager_opts = [
        cfg.StrOpt('glance_pull_topic',
                    default = 'glance_pull',
                    help = 'The topic glance pull nodes listen on'),
]

CONF.register_opts(glance_pull_manager_opts)

from glance import service
from glance import config
from glance import log as logging


if __name__ == "__main__":
    sys.path
    config.parse_args(sys.argv)
    logging.setup("glance")
    server = service.Service.create(binary='glance_pull', topic = CONF.glance_pull_topic)
    service.serve(server)
    service.wait()
