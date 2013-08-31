#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-8-19
#Copyright 2013 nuoqingyun xuqifeng

import os
try:
    import pymongo
except ImportError:
    pymongo = None

try:
    import bson
except ImportError:
    bson = None
import re 
from oslo.config import cfg

from glance.exception import ImproperlyConfigured

mongo_opts = [
        cfg.StrOpt('MONGO',
                    default = 'mongodb://192.168.11.247:27017',
                    help = 'MongoBackend ip & port.'),
]

CONF =  cfg.CONF
CONF.register_opts(mongo_opts)


class MongoBackend():


    internal_collections = ['ports', 'servers','traffic','access_log']

    database = 'glance'


    def __init__(self):
        if not pymongo:
            raise ImproperlyConfigured(
                    "You need to install the pymongo library to use the "
                    "MongoDB backend.")

        self.pymongo = pymongo
        self.url = CONF.MONGO
        self._database = None
        self._connection = None

    def get_connection(self):
        """Connect to the MongoDB server."""
        from pymongo import MongoClient

        if self._connection is None:
            self._connection = MongoClient(host=self.url, max_pool_size=10)

        return self._connection


    def get_database(self, database=None):
        """"Get or create database  """
        database = database if database !=None else self.database
        
        if self._database is None:
            conn = self.get_connection()
            db = conn[database]
            self._database = db
        
        return self._database


    def get_collection(self, collection, append=None, prefix=''):
        db = self.get_database()

        if collection in self.internal_collections or append is False:
            collection = "{0}".format(collection) 
        else:
            collection = "glance_{0}{1}".format(prefix, collection)
            print collection, '44444444444444444444444444444444444444444444'

        collection = db[collection]

        return collection

    def get_server_system_collection(self, server):
        
        name = self.string_to_valid_collection_name(server["key"])
        collection_name = "{0}_system".format(name)
        collection = self.get_collection(collection_name, append=False)

        return collection

    def get_server_processes_collection(self, server):
        
        name = self.string_to_valid_collection_name(server["key"])
        collection_name = "{0}_processes".format(name)
        collection = self.get_collection(collection_name, append=False)

        return collection

    def get_server_portscan_collection(self, server):
        
        name = self.string_to_valid_collection_name(server["key"])
        collection_name = "{0}_portscan".format(name)
        collection = self.get_collection(collection_name, append=False)

        return collection

    def store_entry(self, entry, collection):
        """ Stores a system entry  """

        collection = self.get_collection(collection)

        if collection:
            collection.save(entry, safe=True)   

    def index(self, collection):
        collection = self.get_collection(collection)
        collection.ensure_index([('time', pymongo.DESCENDING)])

    def store_entries(self, entries, server_id=None):
        ''' 
            List with dictionaries, loops through all of them and saves them to the database
            Accepted format:
            {'cpu': {'time': 1313096288, 'idle': 93, 'wait': 0, 'user': 2, 'system': 5}}
        '''
        for key, value in entries.iteritems():
            if server_id != None:
                value['server_id'] = server_id
            self.store_entry(value, key)
            self.index(key)

    def get_object_id(self,id):
        return bson.objectid.ObjectId(id)

    def string_to_valid_collection_name(self, string):
        return re.sub(r'[^\w]', '', str(string)).strip().lower()


backend = MongoBackend()
