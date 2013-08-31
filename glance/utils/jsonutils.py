#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import datetime
import functools
import inspect
import itertools
import json

def object_encoder(value, convert_instances=False, convert_datetime=True,
                   level=0, max_depth=3):
    nasty = [inspect.ismodule, inspect.isclass, inspect.ismethod,
             inspect.isfunction, inspect.isgeneratorfunction,
             inspect.isgenerator, inspect.istraceback, inspect.isframe,
             inspect.iscode, inspect.isbuiltin, inspect.isroutine,
             inspect.isabstract]
    for test in nasty:
        if test(value):
            return unicode(value)
    if type(value) == itertools.count:
        return unicode(value)
    try:
        recursive = functools.partial(object_encoder,
                                      convert_instances = convert_instances,
                                      convert_datetime = convert_datetime,
                                      level = level,
                                      max_depth = max_depth)
        if isinstance(value, (list, tuple)):
            return [recursive(v) for v in value]
        
        elif isinstance(value, dict):
            return dict((k, recursive(v)) for k, v in value.iteritems())
        elif convert_datetime and isinstance(value, datetime.datetime):
            return strtime(value)
        elif hasattr(value, 'iteritems'):
            return recursive(dict(value.iteritems()), level = level + 1)
        else:
            return value
    except TypeError:
        return unicode(value)

def strtime(at=None, format="%Y-%m-%dT%H:%M:%S.%f"):
    if not at:
        at = datetime.datetime.utcnow()
    return at.strftime(format)

def dumps(value, default=object_encoder, **kwargs):
    return json.dumps(value, default=default, **kwargs)

def loads(s):
    return json.loads(s)

def load(s):
    return json.load(s)
