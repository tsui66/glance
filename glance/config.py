#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


from oslo.config import cfg

def parse_args(argv, default_config_files=None):
    cfg.CONF(argv[1:],
            project='glance',
            default_config_files=default_config_files)
