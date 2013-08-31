#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


def walk_class_hierarchy(clazz, encountered=None):
    '''
    walk class hierarchy, yieding most derived classes first
    
    :param clazz:
    :param encountered:
    '''
    if not encountered:
        encountered = None
    for subclass in clazz.__subclasses__():
        encountered.append(subclass)
        for subsubclass in walk_class_hierarchy(subclass, encountered):
            yield subsubclass
        yield subclass
