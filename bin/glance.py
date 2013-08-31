#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-6-7
#Copyright 2013 nuoqingyun xuqifeng


import sys
import time
import os
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), 
                                     os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "glance", '__init__.py')):
        sys.path.insert(0, possible_topdir)
try:
    from glance.glance_agent.api import GlanceAgentAPI
except:
    print 'Glance is not found.'
    sys.exit()
from oslo.config import cfg

from glance.glance_agent import __version__
from glance.utils.daemon import Daemon
from glance import log as logging

glanceagent_opts = [
        cfg.IntOpt('SYSTEM_CHECK_PERIOD',
                    default=60,
                    help = 'check system per 1 minute'),
        cfg.StrOpt('server_key',
                    default = '0.0.0.0',
                    help = 'The passport for glance.'),
        cfg.ListOpt('GlanceSystemList',
                    default = ['cpu', 'network', 'memory', 'disk', 'loadavg'],
                    help = 'The lsit  for glance.'),
]


CONF =  cfg.CONF
CONF.register_opts(glanceagent_opts)
#CONF(project = 'glance')


logging.setup("glance")
LOG = logging.getLogger("glance")
PIDFILE = '/var/run/glance.pid'


class GlanceAgentDaemon(Daemon):

    def __init__(self):
        self.server_key = CONF.server_key
        super(GlanceAgentDaemon, self).__init__(PIDFILE)
        self.glanceagentapi = GlanceAgentAPI()
	
    def start(self):
        try:
            self.glanceagentapi.getServer(self.server_key)
        except:
            LOG.exception("Get server  info failed")
        super(GlanceAgentDaemon, self).start()

    def run(self):
        flag = 2
        while True:
            # Checks the system every 60 seconds
            self.glanceagentapi.getSystem()
            self.glanceagentapi.getProcess(self.server_key)
            self.glanceagentapi.getPortScan()
            if flag == 2 :
                self.glanceagentapi.getTraffic()
                flag = 0 
            time.sleep(CONF.SYSTEM_CHECK_PERIOD)
            flag += 1

if __name__ == "__main__":

    daemon = GlanceAgentDaemon()

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            try:
                daemon.start()
                print "Starting glanceagent {0}...".format(__version__)
            except Exception, e:
                LOG.exception("The agent couldn't be started")
                print str(e)
        elif 'stop' == sys.argv[1]:
            print "Stopping Glance Agent ..."
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print "Restaring Glance Agent ..."
            daemon.restart()
        elif 'status' == sys.argv[1]:
            try:
                pf = file(PIDFILE,'r')
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None
            except SystemExit:
                pid = None

            if pid:
                print 'Glance Agent {0} is running as pid {1}'.format(__version__, pid)
            else:
                print 'Glance Agent is not running.'

        else:
            print "Unknown command"
            sys.exit(2)
            sys.exit(0)
    else:
        print "usage: %s start|stop|restart|status" % sys.argv[0]
        sys.exit(2)

