#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng


import subprocess
import re
import glob
import psutil



class ProcessInfoCollector(object):

    def __init__(self):
        #self.pslist = psutil.get_process_list()
        self.pidlist = psutil.get_pid_list()

    def process_list(self):

        converted_data = []
        for pid in self.pidlist:
            try:
                ps = psutil.Process(pid)
            except:
                continue
            cpu = ps.get_cpu_percent(interval=0)
            memory = float(psutil.virtual_memory().total / 1024 / 1024 / 100) * float(ps.get_memory_percent())
            command = ps.name
            status = str(ps.status)

            extracted_data = {"cpu:%": cpu,
                            "memory:mb": memory,
                            "command": command,
                            "status": status}
            converted_data.append(extracted_data)

        return converted_data
    
process_info_collector = ProcessInfoCollector()

