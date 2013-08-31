#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import os
import errno
import commands


def ensure_tree(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            if not os.path.isdir(path):
                raise
        raise

def write_to_file(file, mode, data):
    with open(file, mode) as f:
        f.write("\n")
        f.write(data)

def get_dir_size(path):
    ensure_tree(path)
    cmd = "du -sh %s" % path
    
    result = commands.getoutput(cmd).split()[0]
    result = result[:-1]
    if result:
        result = int(result)
    else:
        result =0
    return result
    
    

