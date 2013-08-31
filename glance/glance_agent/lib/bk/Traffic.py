#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-6-8
#Copyright 2013 nuoqingyun xuqifeng

import re
import time
from urlparse import urlparse
from oslo.config import cfg

from glance.db.mongo.models import TrafficModel

gather_opts = [
        cfg.StrOpt('access_log_file',\
                    default = '/home/mepoo/glance/trunk/glance/heartbeat/db/mongo/tests/access.log',
                    help = "Path of access_log_file"),
        ]
CONF = cfg.CONF
CONF.register_cli_opts(gather_opts)

class GatherLogData(object):
    def __init__(self):
        self.traffic_model = TrafficModel()

    def gather_log(self):
        #logs =[]
        HITS_CODE = ["TCP_HIT", "TCP_REFERSH_HIT", "TCP_IMS_HIT", "TCP_MEM_HIT", "UDP_HIT"]
        for line in open(CONF.access_log_file, 'r'):
            if line.strip() == '':
                continue
            data = re.split('\s+', line)
            #logs.append(data)
            # Separating data.
            clinet_ip = data[0]
            bytes = int(data[1])
            #log_time = time.strftime('%Y-%m-%d %H:%M:%S', \
            #        time.localtime(float(data[2]))) 
            log_time = float(data[2])
            #method = data[3]
            url = data[4] 
            responsetime = data[6]
            responsecode = data[11]
            referer = data[12] 
            hit_code = data[13]
            code = (hit_code.split(':')[0] in HITS_CODE ) and 1 or 0
            # Separate URL
            domain, path = urlparse(url)[1:3]
            referer_domain, referer_path = urlparse(referer)[1:3]
            print "ready data"
            traffic = {"log_time":log_time, "domain":domain, "bytes":bytes, \
                    "hit_code":hit_code, "code":code,  "responsetime":responsetime, \
                            "responsecode":responsecode,"clinet_ip":clinet_ip\
                        }
            print "start mongo"
            self.traffic_model.add(traffic, "log_time")
            print "end"

        return traffic
gatherlogdata = GatherLogData()
