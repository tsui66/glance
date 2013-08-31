
import eventlet
eventlet.monkey_patch(os=False)

import os
import sys


from oslo.config import cfg
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
                    sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "appengine", "__init__.py")):
    sys.path.insert(0, possible_topdir)

opts = [ 
        cfg.StrOpt('bind_host', default='0.0.0.0'),
        cfg.IntOpt('bind_port', default=9292),
]
CONF = cfg.CONF
CONF.register_opts(opts) 


if __name__ == "__main__":
    print sys.argv[1:]
    CONF(project = 'test')
    print CONF.bind_port 
