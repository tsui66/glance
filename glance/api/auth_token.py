#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng

import httplib
import datetime
import json
import time
import urllib

from oslo.config import cfg  # @UnresolvedImport

from glance.utils import memcached  # @UnresolvedImport
from glance.utils import jsonutils  # @UnresolvedImport

opts = [
    cfg.StrOpt('auth_admin_prefix', default=''),
    cfg.StrOpt('auth_host', default='127.0.0.1'),
    cfg.IntOpt('auth_port', default=2345),
    cfg.StrOpt('auth_protocol', default='https'),
    cfg.StrOpt('auth_uri', default=None),
    cfg.StrOpt('auth_version', default=None),
    cfg.BoolOpt('delay_auth_decision', default=False),
    cfg.BoolOpt('http_connect_timeout', default=None),
    cfg.StrOpt('http_handler', default=None),
    cfg.StrOpt('admin_token', secret=True),
    cfg.StrOpt('admin_user'),
    cfg.StrOpt('admin_password', secret=True),
    cfg.StrOpt('admin_tenant_name', default='admin'),
    cfg.StrOpt('cache', default=None),   # env key for the swift cache
    cfg.StrOpt('certfile'),
    cfg.StrOpt('keyfile'),
    cfg.StrOpt('signing_dir'),
    cfg.ListOpt('memcached_servers', 
                default = ["127.0.0.1:11211"],
                deprecated_name='memcache_servers'),
    cfg.IntOpt('token_cache_time', default=300),
    cfg.IntOpt('revocation_cache_time', default=1),
    cfg.StrOpt('memcache_security_strategy', default=None),
    cfg.StrOpt('memcache_secret_key', default=None, secret=True)
]

CONF = cfg.CONF
CONF.register_opts(opts, group="Auth")

CACHE_KEY_TEMPLATE='tokens/%s'

class MiniResp(object):
    def __init__(self, error_message, env, headers=[]):
        if env['REQUEST_METHOD'] == 'HEAD':
            self.body = ['']
        else:
            self.body = [error_message]
        self.headers = list(headers)
        self.headers.append(('Context-type', 'text/plain'))
    
    
class AuthProtocol(object):
    
    def _assert_valid_memecache_protection_config(self):
        if self._memcache_security_strategy:
            if self._memcache_security_strategy not in('MAC', 'ENCRYPT'):
                raise
            if not self._memcache_secret_key:
                raise
              
    def __init__(self, app, conf):
        self.app = app
        self.conf = conf
        
        self.delay_auth_decision = True
        self.auth_host = self._conf_get('auth_host')
        self.auth_port = self._conf_get("auth_port")
        self.auth_protocol = self._conf_get("auth_protocol")
        
        if self.auth_protocol == "http":
            self.http_client_class = httplib.HTTPConnection
        else:
            self.http_client_class = httplib.HTTPSConnection
        
        self.auth_admin_prefix = self._conf_get("auth_admin_prefix")
        self.auth_uri = self._conf_get("auth_uri")
        
        if self.auth_uri is None:
            self.auth_uri = "%s://%s:%s" %(self.auth_protocol,
                                           self.auth_host,
                                           self.auth_port)
        self.cert_file = self._conf_get("certfile")
        self.key_file = self._conf_get("keyfile")
        self.signing_dirname = self._conf_get("signing_dir")
        
        self.admin_token = self._conf_get("admin_token")
        self.admin_token_expiry = None
        self.admin_user = self._conf_get("admin_user")
        self.admin_password = self._conf_get("admin_password")
        self.admin_tenant_name = self._conf_get("admin_tenant_name")
        
        self._cache = None
        self._cache_initialized = False
        self._memcache_security_strategy = self._conf_get("memcache_security_strategy")
        if self._memcache_security_strategy :
            self._memcache_security_strategy - self._memcache_security_strategy.upper()
        self._memcache_secret_key = \
            self._conf_get('memcache_secret_key')
        self._assert_valid_memecache_protection_config()
        self.token_cache_time = int(self._conf_get("token_cache_time"))
        self._token_revication_list = None
        self._token_revication_list_fetched_time = None
        self.token_revocation_list_cache_timeout = datetime.timedelta(
                                                seconds=self._conf_get("revocation_cache_time"))
        http_connect_timeout_cfg = self._conf_get("http_connect_timeout")
        self.http_connection_timeout = (http_connect_timeout_cfg and
                                        int(http_connect_timeout_cfg))
        self.auth_version = None
           
    def _init_cache(self, env):
        cache = self._conf_get('cache')
        memcache_servers = self._conf_get('memcached_servers')
        if cache and env.get(cache, None) is not None:
            self._cache = env.get(cache)
        else:
            self._cache = memcached.get_client(memcache_servers)
        self._cache_initialized = True
    
    def _conf_get(self, name):
        if name in self.conf:
            return self.conf[name]
        else:
            return CONF.Auth[name]
    
    def _get_user_token_from_header(self, env):
        token = self._get_header(env, 'X-Auth-Token',
                                 self._get_header(env, 'X-Storage-Token'))
        if token:
            return token
        else:
            if not self.delay_auth_decision:
                raise InvalidUserToken('Unable to find token in headers')
    
    def _get_header(self, env, key, default=None):
        env_key = self._header_to_env_var(key)
        return env.get(env_key, default)
    
    def _add_headers(self, env, user_headers):
        for(k, v) in user_headers.iteritems():
            env_key = self._header_to_env_var(k)
            env[env_key] = v
      
    def _build_user_headers(self, token_info):
        user = token_info['accepted']['user']
        token = token_info['accepted']['token']
        
        user_name = user['name']
        user_id = user['id']
        
        rval = {
            'X-User-Name': user_name,
            'X-User-id': user_id,
            'X-User': user_name
        }
        return rval
              
    def _header_to_env_var(self, key):
        return 'HTTP_%s' % key.replace('-', '_').upper()
      
    def _remove_headers(self, env, auth_headers):
        for key in auth_headers:
            env_key = self._header_to_env_var(key)
            try:
                del env[env_key]
            except KeyError:
                pass
     
    def _remove_auth_headers(self, env):
        auth_headers = (
            'X-User-Id',
            'X-User-Name',
            'X-User',
            )
        self._remove_headers(env, auth_headers)
        

    def verify_uuid_token(self, user_token, retry=True):
        headers = {
            'X-Auth-Token': self.get_admin_token(),
            'X-Subject-Token': safe_quote(user_token)
            }
        response, data = self._json_request('GET',
                        '/auth/tokens',
                        additional_headers=headers)
        if response.status == 200:
            return data
        if response.status == 404:
            raise InvalidUserToken('Token authorization failed')
        if response.status == 401:
            self.admin_token = None
        if retry:
            return self._validate_user_token(user_token, False)
        else:
            return InvalidUserToken()
        
    def get_admin_token(self):
        if self.admin_token_expiry:
            pass
        if not self.admin_token:
            (self.admin_token,
            self.admin_token_expiry) = self._request_admin_token()
        return self.admin_token
    

    def _json_request(self, method, path, body=None, additional_headers=None):
        kwargs = {
            'headers':{
                'Content-type': 'application/json',
                'Accept': 'application/json'
                    }
                }
        
        if additional_headers:
            kwargs['headers'].update(additional_headers)
        if body:
            kwargs['body'] = jsonutils.dumps(body)
        path = self.auth_admin_prefix + path
        response, body = self._http_request(method, path, **kwargs)
        try:
            data = json.loads(body)
        except ValueError:
            data = {}
        return response, data
    
    def _http_request(self, method, path, **kwargs):
        conn = self._get_http_connection()
        RETRIES = 3
        retry = 0
        while True:
            try:
                conn.request(method, path, **kwargs)
                response = conn.getresponse()
                body = response.read()
                break
            except Exception as e:
                if retry == RETRIES:
                    raise ServiceError('unable to communicat with auth')
                time.sleep(2.0 ** retry /2)
                retry += 1
            finally:
                conn.close()
        return response, body
    
    def _get_http_connection(self):
        if self.auth_protocol == 'http':
            return self.http_client_class(self.auth_host,
                                          self.auth_port,
                                          timeout=self.http_connection_timeout)
        else:
            return self.http_client_class(self.auth_host,
                                          self.auth_port,
                                          self.key_file,
                                          self.cert_file,
                                          timeout=self.http_connection_timeout)
    
    def _request_admin_token(self):
        params = {
            'auth':{
                'passwordCred':{
                    'username': self.admin_user,
                    'password': self.admin_password
                            }
                }
            }
        response, data = self._json_request('POST',
                            '/auth/tokens',
                            body=params            
                            )
        try:
            token = data['accepted']['token']['id']
            expiry = data['accepted']['token']['expires']
            if not (token and expiry):
                raise AssertionError('invalid token or expires')
            #datetime_expires =data
            return (token, expiry)
        except (AssertionError, KeyError):
            raise ServiceError('invalid json response')
        except ValueError:
            raise ServiceError('invalid json response')
        
    
    def _cache_store_invalid(self, user_token):
        if self._cache:
            self._cache_store(user_token, "invalid")
    
    
    def _confirm_token_not_expired(self, data):
        if not data:
            raise InvalidUserToken('Token authorization failed')
        expires = data['accepted']['token']['expires']
        fmt = "%Y-%m-%d %H:%M:%S"
        expires = datetime.datetime.strptime(expires, fmt)
        if datetime.datetime.utcnow() > expires:
            raise InvalidUserToken('Token authorization failed')
        return expires
    
    def _validate_user_token(self, user_token, retry=True):
        try:
            token_id = user_token
            cached = self._cache_get(token_id)
            if cached:
                return cached
            data = self.verify_uuid_token(user_token, retry)
            expires = self._confirm_token_not_expired(data)
            self._cache_put(token_id, data, expires)
            return data
        except Exception as e:
            self._cache_store_invalid(user_token)
            raise InvalidUserToken('Token authorization failed')
    
    def _cache_get(self, token, ignore_expires=False):
        if self._cache and token:
            key = CACHE_KEY_TEMPLATE % token
            serialized = self._cache.get(key)
            
            if serialized is None:
                return None
            cached = json.loads(serialized)
            if cached == 'invalid':
                raise InvalidUserToken('Token authorization failed')
            data, expires = cached
            fmt = "%Y-%m-%dT%H:%M:%S.%f"
            expires = datetime.datetime.strptime(expires, fmt)
            if datetime.datetime.utcnow() < expires:
                return data
            else:
                pass
    
    def _cache_put(self, token, data, expires):
        if self._cache:
            self._cache_store(token, (data, expires))
    
    def _cache_store(self, token, data):
        serialized_data = jsonutils.dumps(data)
        cache_key = CACHE_KEY_TEMPLATE % token
        try:
            self._cache.set(cache_key,
                            serialized_data,
                            time = self.token_cache_time)
        except KeyError:
            self._cache.set(cache_key,
                            serialized_data,
                            timeout = self.token_cache_time)
             
    def __call__(self, env, start_response):
        if not self._cache_initialized:
            self._init_cache(env)
        try:
            self._remove_auth_headers(env)
            user_token = self._get_user_token_from_header(env)
            token_info = self._validate_user_token(user_token)
            env['auth.token_info'] = token_info
            user_headers = self._build_user_headers(token_info)
            self._add_headers(env, user_headers)
            return self.app(env, start_response)
        except InvalidUserToken:
            if self.delay_auth_decision:
                self._add_headers(env, {"X-Identity-Status": "Invalid"})
                return self.app(env, start_response)
            else:
                return self._reject_reuqest(env, start_response)
        except ServiceError:
            resp = MiniResp('Service unavailable', env)
            start_response('503 Service unavailable', resp.headers)
            return resp.body
        
            
class InvalidUserToken(Exception):
    pass


class ServiceError(Exception):
    pass

def safe_quote(s):
    return (urllib.quote(s) if s == urllib.unquote(s) else s)
    
    
def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    
    def auth_filter(app):
        return AuthProtocol(app, conf)
    return auth_filter


            
