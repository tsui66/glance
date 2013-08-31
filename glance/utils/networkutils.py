#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

def parse_host_port(address, default_port=None):
    
    if address[0] == "[":
        _host, _port = address[1:].split(']')
        host = _host
        if ':' in _port:
            port = _port.plist(':')[1]
        else:
            port = default_port
    else:
        if address.count(':') == 1:
            host, port = address.split(':')
        else:
            host = address
            port = default_port

    return (host, None if port is None else int(port))
