#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import gc
import pprint
import sys
import traceback

import eventlet 
import eventlet.backdoor
import greenlet
from oslo.config import cfg

eventlet_backdoor_opts=[
        cfg.IntOpt("backdoor_opt",
                   default=None,
                   help="port for eventlet backdoor to listent")
            ]

CONF = cfg.CONF
CONF.register_opts(eventlet_backdoor_opts)


def _dont_use_this():
    print "dont use this"


def _find_objects(t):
    return filter(lambda o:isinstance(o, t), gc.get_objects())


def _print_greenthreads():
    for i, gt in enumerate(_find_objects(greenlet.greenlet)):
        print i, gt
        traceback.print_stack(gt.gr_frame)
        print


def _print_nativethreads():
    for threadId, stack in sys._current_frames().items():
        print threadId
        traceback.print_stack(stack)
        print

def initialize_if_enabled():
    backdoor_locals ={
        'exit': _dont_use_this,
        'quit': _dont_use_this,
        'fo': _find_objects,
        'pgt': _print_greenthreads,
        'pnt': _print_nativethreads            
        }
