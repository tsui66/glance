#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-6-8
#Copyright 2013 nuoqingyun xuqifeng


import eventlet


from glance.utils import processutils


def excute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    if 'run_as_root' in kwargs and not 'root_helper' in kwargs:
        kwargs['root_helper'] = 'sudo'
    return processutils.execute(*cmd, **kwargs)

def trycmd(*cmd, **kwargs):
    """Convenience wrapper around oslo's trycmd() method."""
    return processutils.trycmd(*cmd, **kwargs)

def spawn_n(func, *args, **kwargs):
    """
    Passthrough method for eventlet.spawn_n.

    This utility exists so that it can be stubbed for testing without
    interfering with the service spawns.
    """
    eventlet.spawn_n(func, *args, **kwargs)
    
