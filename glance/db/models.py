#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-8-19
#Copyright 2013 nuoqingyun xuqifeng

from datetime import datetime
import calendar
import random
import string
import uuid
from oslo.config import cfg

from glance.db.basemodel import BaseModel
from glance.db.js import traffic_map_test, traffic_reduce_test
from glance.utils import timeutils
from glance import log as logging

LOG = logging.getLogger(__name__)

mongo_opts = [
        cfg.StrOpt('out_collection',
                    default = 'out',
                    help = 'A name of collection which is the result of the map-reduce operation'),
        ]
CONF = cfg.CONF
CONF.register_opts(mongo_opts)

class ApiModel(BaseModel):

    def __init__(self):
        self.process_table_created = 0
        super(ApiModel, self).__init__()
    
    #Used in the collector, saves all the data in UTC
    def unix_utc_now(self):
        self.d = datetime.utcnow()
        _unix = calendar.timegm(self.d.utctimetuple())

        return _unix

    def check_server_key(self, server_key):
        print "check_server_key"
        collection = self.mongo.get_collection('servers')
        print server_key
        server = collection.find_one({"key": server_key})
    
        return server

    def server_update_disk_volumes(self, server_key, volumes):
        try:
            volume_data = volumes.keys()
        except:
            volume_data = False

        if volume_data:
            valid_volumes = filter(lambda x: x not in ['time','last'], volume_data)
            
            collection = self.mongo.get_collection('servers')
            collection.update({"key": server_key}, {"$set": {"volumes": valid_volumes}})

    
    def server_update_network_interfaces(self, server_key, interfaces):
        try:
            interfaces_data = interfaces.keys()
        except:
            interfaces_data = False
       
        if interfaces_data:
            valid_adapters = filter(lambda x: x not in ['time','last','lo'], interfaces_data)
            
            collection = self.mongo.get_collection('servers')
            collection.update({"key": server_key}, {"$set": {"network_interfaces": valid_adapters}})

    def server_update_last_check(self, server_key, last_check):
        collection = self.mongo.get_collection('servers')
        collection.update({"key": server_key}, {"$set": {"last_check": last_check}})

    def server_update_uptime(self, server_key, uptime):
        collection = self.mongo.get_collection('servers')
        collection.update({"key": server_key}, {"$set": {"uptime": uptime}})
           
    def server_update_processes(self, server_key, processes):
        collection = self.mongo.get_collection('servers')
        server = collection.find_one({"key": server_key})
        existing_processes =  server.get('processes', [])
        updated_list =  list(set(existing_processes).union(processes))
        
        cleaned_list = []
        for element in updated_list:
            if element.find("/") ==-1:
                cleaned_list.append(element)

        collection.update({"key": server_key}, {"$set": {"processes": cleaned_list}})


    def store_system_entries(self, server_key, data):
        print server_key
        server = self.check_server_key(server_key)
        print server

        if server:
            data["time"] = self.unix_utc_now()

            self.server_update_disk_volumes(server_key, data.get('disk',None))
            self.server_update_network_interfaces(server_key, data.get('network',None))
            self.server_update_last_check(server_key, data['time'])
            self.server_update_uptime(server_key, data.get('uptime', None))
            
                        
            collection = self.mongo.get_server_system_collection(server)
            collection.insert(data)
            collection.ensure_index([('time', self.desc)])
        

    def store_process_entries(self, server_key, data):
        server = self.check_server_key(server_key)
        if server:
            collection = self.mongo.get_server_processes_collection(server)
            #self.server_update_processes(server_key, data.keys())
            
            data_dict = {}
            #map(lambda x: data_dict.update(x), for x in data)
            time = self.unix_utc_now()
            data_dict['time'] = time
            data_dict['processes'] = data
            
            collection.insert(data_dict)
            collection.ensure_index([('time', self.desc)])

    def store_portscan_entries(self, server_key, data):
        server = self.check_server_key(server_key)

        if server:
            print "store_portscan_entries"
            data["time"] = self.unix_utc_now()
            data['key'] = server_key
            if self.process_table_created == 0:
                collection = self.mongo.get_server_portscan_collection(server)
                process = collection.find_one({'key': server_key})
                print process
                #self.process_table_created = process.get("time", 0) and  1 or 0
                self.process_table_created = process and 1 or 0
                print collection
                print "sssssssssssssssssssssssssssssss"
                print self.process_table_created
            if self.process_table_created:
                print "sssssssssssssssssssssssssssssss"
                collection.update({"key": server_key}, {"$set": data})
            else:
                collection.insert(data)
                collection.ensure_index([('time', self.desc)])
     

class SystemModel(BaseModel):

    def __init__(self):
        super(SystemModel, self).__init__()

    def get_system_data(self, charts, date_from, date_to, server):
        collection = self.mongo.get_server_system_collection(server)
        data_dict = collection.find({"time":{"$lte": date_to}}).sort('time', self.asc)
        filtered_data = {'memory': [], "cpu": [], "disk": [], "network": [], "loadavg": []}

        # Get data for all charts
        if len(charts) == 0:
            charts = filtered_data.keys()

        for line in data_dict:
            #time = line['time']
            for element in filtered_data:
                if element in charts:
                    #line[element]["time"] = time
                    filtered_data[element].append(line[element])
        return filtered_data

class ServerModel(BaseModel):

    def __init__(self):
        super(ServerModel, self).__init__()
        self.collection = self.mongo.get_collection('servers')
    
    def generate_random_string(size=6, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))

    def server_exists(self, name):
        result = self.collection.find({"hostname": name}).count()

        return result


    def add(self, data, *agrs, **kwargs):
        #server_key  = self.generate_random_string(size=32)
        #server_key = uuid.uuid1()
        server_key = data['key']
        data["key"] = server_key
        
        self.collection.insert(data)
        self.collection.ensure_index([('key', self.desc)])

        return server_key

    def get_all(self):
        count = self.collection.find().count()

        if count == 0:
            return None
        else:
            server =  self.collection.find(sort=[("hostname", self.asc), ("last_check", self.asc) ])
            return server

    def get_filtered(self, filter=None):
        if filter == 'all':
          return self.get_all()
        
        if filter != False:
            servers_list = []
            
            # Append only existing servers
            for server in filter:
                #try:
                #    server_id = self.mongo.get_object_id(server)
                #except:
                #    server_id = False

                #if server_id != False:
                #    servers_list.append({'_id': server_id})
                servers_list.append({'_id': server['_id']})
            print servers_list, '&&&&&&&&&&&&&&&&&&&&&&&&&&&'
            if len(servers_list) > 0:
                return self.collection.find({'$or': servers_list})


    def get_server_by_key(self, key):
        return self.collection.find_one({"key": key})

    def delete(self, id):

        server = self.get_by_id(id)

        # Delete data 
        system_collection = self.mongo.get_server_system_collection(server)
        system_collection.drop()

        process_collection = self.mongo.get_server_processes_collection(server)
        process_collection.drop()

        portscan_collection = self.mongo.get_server_portscan_collection(server)
        portscan_collection.drop()

        try:
            object_id =  self.mongo.get_object_id(id)
        except:
            object_id = False

        if object_id:
            self.collection.remove(object_id)
    

    def get_all_dict(self):
        servers_dict = {}
        servers = self.collection.find()
        for server in servers.clone():
            id = str(server['_id'])
            del server['_id']
            servers_dict[id] = server

        return servers_dict


    # Group methods 
    def get_servers_for_group(self, group_id):
        result = self.collection.find({"alert_group": str(group_id)})

        return result

class TrafficModel(BaseModel):
    def __init__(self):
        super(TrafficModel, self).__init__()
        self.collection = self.mongo.get_collection("traffic")
        self.out_collection_name = self.collection.name + CONF.out_collection

    #CURD
    def add(self, sets=None, index=None, *args, **kwargs):
        if sets:
            self.collection.insert(sets)
            ###self.collection.ensure_index([('log_time', self.desc)])
            self.collection.ensure_index([(index, self.desc)])
    
    def get_all(self, *args, **kwargs):
        count = self.collection.find().count()

        if count == 0:
            return None
        else:
            return self.collection.find()

    def get_traffic_by_domain(self, date, domain, *arg, **kwargs):
        result = []
        out_collection_name = 'traffic_' + date
        print out_collection_name
        traffic_out_collection = self.mongo.get_collection(out_collection_name, append=False)
        if domain:
            for traffic in traffic_out_collection.find({'_id': domain}).clone():
                result.append({'domain': traffic['_id'], 'value': traffic['value']})
        else:
            trafficsum = traffic_out_collection.find()
            for traffic in trafficsum:
                result.append({'domain': traffic['_id'], 'value': traffic['value']})

        return result

    def unix_utc_now(self):
        self.d = datetime.utcnow()
        _unix = calendar.timegm(self.d.utctimetuple())

        return _unix

    def update_traffic_detail_by_time(self, *args, **kwargs):
        now = self.unix_utc_now() 
        minute = now - 60
        hour = now - 3600
        day = timeutils.get_day_begin()
        week = timeutils.get_week_begin()
        month = timeutils.get_month_begin()
        def update_traffic((date_from, date_to, out_collection_name)):
            time_query = {
                "log_time":
                    {
                        "$gte": date_from,
                        "$lte": date_to
                    }
                }
            self.collection.map_reduce(traffic_map_test, traffic_reduce_test, 
                            out=out_collection_name, query=time_query)
        update_list = [(month, now, 'traffic_month'), 
                        (day, now, 'traffic_day'), 
                        (week, now, 'traffic_week'), 
                        (hour, now, 'traffic_hour'),
                        (minute, now, 'traffic_minute')]
        map(lambda tup: update_traffic(tup), update_list)

    def get_traffic_by_date(self, *args, **kwargs):
        pass

class AccessLogModel(BaseModel):
    def __init__(self):
        super(AccessLogModel, self).__init__()

class PortScanModel(BaseModel):
    def __init__(self):
        super(PortScanModel, self).__init__()
        self.collection = self.mongo.get_collection("PortScan")

    #CURD
    def add(self, sets=None, index=None, *args, **kwargs):
        if sets:
            self.collection.insert(sets)
            self.collection.ensure_index([(index, self.desc)])
    
    def get_all(self, *args, **kwargs):
        count = self.collection.find().count()

        if count == 0:
            return None
        else:
            return self.collection.find()

    def get_portstate_by_domain(self, domain, *args, **kwargs):
        try:
            result = self.collection.find({'domain': domain})
            return result
        except Exception as e:
            print str(e)
            LOG.error(str(e))

    def get_portstate_by_domainlist(self, domainlist, *args, **kwargs):
        try:
            result = []
            for domain in domainlist:
                portscan_collection = self.mongo.get_server_portscan_collection(domain)
                port_result = portscan_collection.find(domain)
                for port in port_result.clone():
                    result.append({'host':port['host'], 'key': port['key'], 'scan': port['scan'], 'time':port['time']})
            return result
        except Exception as e:
            print str(e)
            LOG.error(str(e))


class ProcessModel(BaseModel):
    def __init__(self):
        super(ProcessModel, self).__init__()

    def get_server_processes(self, server, date_to):
        self.process_collection = self.mongo.get_server_processes_collection(server)
        result = []
        #data =  self.process_collection.find()
        data = self.process_collection.find({"time":{"$lte": date_to}}).sort('time', self.asc)
        for process in data:
            del process['_id']
            #result.append(process)
            process['key'] = server['key']
            #result = process.update(server)
            result = process
            return result

system_model = SystemModel()
api_model = ApiModel()
traffic_model = TrafficModel()
server_model = ServerModel()
access_log_model = AccessLogModel()
portscan_model = PortScanModel()
process_model = ProcessModel()
