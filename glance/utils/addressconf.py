#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import socket

from oslo.config import cfg

CONF = cfg.CONF

def _get_my_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8',80))
        (addr, port) = sock.getsockname()
        sock.close()
        return addr
    except socket.error:
        return "127.0.0.1"

addr_opts = [
    cfg.StrOpt('my_ip',
               default = _get_my_ip(),
               help="this machine's public address"),
    cfg.StrOpt('host',
               default = socket.gethostname(),
               help="Name of this machine"),
    cfg.StrOpt('use_ipv6',
               default=False,
               help="use_ipv6")
    ]

CONF.register_opts(addr_opts)
