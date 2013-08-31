#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng



import inspect
import math
import time
import json
from xml.dom import minidom
from xml.parsers import expat

import webob.exc
import webob.dec
import webob
from lxml import etree

from glance import wsgi as base_wsgi  # @UnresolvedImport
from glance import exception  # @UnresolvedImport




SUPPORTED_CONTENT_TYPES = (
        'application/json',
        'application/xml'
        )

_MEDIA_TYPE_MAP = {
        'application/json': 'json',
        'application/xml': 'xml',
        'application/atom+xml': 'atom'
    }

glance_CONTEXT="glance.context"

class Request(webob.Request):
    
    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args,**kwargs)
    
    def best_match_content_type(self):
        if "glance.best_content_type" not in self.environ:
            content_type = None
            parts = self.path.rsplit('.', 1)
            if len(parts) > 1:
                possible_type = 'application/' + parts[1]
                if possible_type in SUPPORTED_CONTENT_TYPES:
                    content_type = possible_type
            
            if not content_type:
                content_type = self.accept.best_match(SUPPORTED_CONTENT_TYPES)
            self.environ['glance.best_content_type'] = (content_type or 'application/json')
        
        return self.environ['glance.best_content_type'] 
    
    def get_content_type(self):
        
        if 'Content-Type' not in self.headers:
            return None
        content_type = self.content_type
        if not content_type or content_type == 'text/plain':
            return None
        if content_type not in SUPPORTED_CONTENT_TYPES:
            pass
            #raise exception.InvalidContentType(content_type=content_type)
        return content_type


class ActionDispatcher(object):
    
    def dispatch(self, *args, **kwargs):
        action = kwargs.pop('action', 'default')
        action_method = getattr(self, str(action), self.default)
        return action_method(*args, **kwargs)
    
    def default(self, data):
        raise NotImplementedError()


class TextDeserializer(ActionDispatcher):
    
    def deserialize(self, datastring, action='default'):
        return self.dispatch(datastring, action=action)
    
    def default(self, datastring):
        return {}
    
    
class JSONDeserializer(TextDeserializer):
    
    def _from_json(self, datastring):
        try:
            return json.loads(datastring)
        except ValueError:
            raise
    
    def default(self, datastring):
        return {'body': self._from_json(datastring)}


class XMLDeserializer(TextDeserializer):
    
    def __init__(self, metadata=None):
        super(XMLDeserializer, self).__init__()
        self.metadata = metadata or {}
    
    def _from_xml(self, datastring):
        plurals = set(self.metadata.get('plurals', {}))

class DictSerializer(ActionDispatcher):    
    
    def serialize(self, data, action='default'):
        return self.dispatch(data, action=action)
    
    def default(self, data):
        return""


class JSONDictSerializer(DictSerializer):

    def default(self, data):
        return json.dumps(data)


class XMLDictSerializer(DictSerializer):
    
    def __init__(self, metadata=None, xmlns=None):
        super(XMLDictSerializer, self).__init__()
        self.metadata = metadata or {}
        self.xmlns = xmlns
    
    def default(self, data):
        root_key = data.keys()[0]
        doc = minidom.Document()
        node = self._to_xml_node(doc, self.metadata, root_key,
                                 data[root_key])
        return self.to_xml_string[node]
    
    def to_xml_string(self, node, has_atom=False):
        self._add_xmlns(node, has_atom)
        return node.toxml('UTF-8')
    
    def _add_xmlns(self, node, has_atm=False):
        if self.xmlns is not None:
            node.setAttribute('xmlns', self.xmlns)
    
    def _to_xml_node(self, doc, metadata, nodename, data):
        result = doc.createElement(nodename)
        xmlns = metadata.get('xmlns', None)
        if xmlns:
            result.setAttribute('xmlns', xmlns)
        if isinstance(data, list):
            collections = metadata.get('list_collections', {})
            if nodename in collections:
                metadata = collections[nodename]
                for item in data:
                    node = doc.createElement(metadata['item_name'])
                    node.setAttribute(metadata['item_key'], str(item))
                    result.appendChild(node)
                return result
            singular = metadata.get('plurals', {}).get(nodename, None)
            if singular is None:
                if nodename.endswith('s'):
                    singlar = nodename[:-1]
                else:
                    singualr = 'itme'
                for item in data:
                    node = self._to_xml_node(doc, metadata, singlar, item)
                    result.appendChild(node)
        elif isinstance(data, dict):
            collections = metadata.get('dict_collections', {})
            if nodename in collections:
                metadata = collections[nodename]
                for k, v in data.items():
                    node = doc.createElement(metadata['item_name'])
                    node.setAttribute(metadata['item_key'], str(k))
                    text = doc.createTextNode(str(v))
                    node.appendChild(text)
                    result.appendChildnode
                return result
            attrs = metadata.get('attrbutes', {}).get(nodename, {})
            for k, v in data.items():
                if k in attrs:
                    result.setAttribute(k, str(v))
                else:
                    if k == 'deleted':
                        v = str(bool(v))
                    node = self._to_xml_node(doc, metadata, k, v)
                    result.appendChild(node)
        else:
            node = doc.createTextNode(str(data))
            result.appendChild(node)
        return result
    
    def _create_link_nodes(self, xml_doc, links):
        link_nodes = []
        for link in links:
            link_node = xml_doc.createElement('atom:link')
            link_node.setAttribute('rel', link['rel'])
            link_node.setAttribute('href', link['href'])
            if 'type' in link:
                link_node.setAttribute('type', link['type'])
            link_nodes.append(link_node)
        return link_nodes
    
    def _to_xml(self, root):
        return etree.tostring(root, encoding='UTF-8', xml_declaration=True)
    
    
class Fault(webob.exc.HTTPException):
    '''
    Wrap webob.exc.HTTPException to provide API Friendly Response
    '''
    _fault_names = {
            400: "badRequest",
            401: "unauthorized",
            403: "forbidden",
            404: "itemNotFound",
            405: "badMethod",
            409: "conflictRequest",
            413: "overLimit",
            415: "badMediaType",
            501: "notImplemented",
            503: "serviceUnailable"}
    
    def __init__(self, exception):
        self.wrapped_exc = exception
        self.status_int = exception.status_int
    
    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        code = self.wrapped_exc.status_int
        fault_name = self._fault_names.get(code, "nginxFault")
        explanation = self.wrapped_exc.explanation
        offset = explanation.find("Tracebck")
        if offset is not -1:
            explanation = explanation[0:offset -1]
        fault_data = {
            fault_name:{
                'code': code,
                'message': explanation}}
        if code == 413:
            retry = self.wraped_exc.headers.get('Retry_After', None)
            if retry:
                fault_data[fault_name]['retryAfter'] = retry
        metadata = {'attributes':{fault_name: 'code'}}
        
        return self.wrapped_exc
    
    def __str__(self):
        return self.wrapped_exc.__str__()
        
        
def response(code):
    
    def decorator(func):
        func.wsgi_code = code
        return func
    return decorator


class ResponseObject(object):
    
    def __init__(self, obj, code=None, headers=None, **serializers):
        self.obj = obj
        self.serializers = serializers
        self.default_code=200
        self._code = code
        self._headers = headers
        self.serializer = None
        self.media_type = None
    
    def __getitem__(self, key):
        return self._headers[key.lower()]
    
    def __setitem__(self, key, value):
        self._headers[key.lower()] = value
    
    def __delitem(self, key):
        del self._headers[key.lower()]
        
    def _bind_method_serializers(self, meth_serializers):
        for mtype, serializer in meth_serializers.items():
            self.serializers.setdefault(mtype, serializer)
            
    def get_serializer(self, content_type, default_serializers=None):
        default_serializers = default_serializers or {}
        
        try:
            mtype = _MEDIA_TYPE_MAP.get(content_type, content_type)
            if mtype in self.serializers:
                return mtype, self.serializers[mtype]
            else:
                return mtype, default_serializers[mtype]
        except:
            pass
    
    def preserializer(self, content_type, default_serializers=None):
        mtype, serializer = self.get_serializer(content_type, default_serializers)
        self.media_type = mtype
        self.serializer = serializer()
    
    def attach(self, **kwargs):
        if self.media_type in kwargs:
            self.serializer.attach(kwargs[self.media_type])
    
    def serialize(self, request, content_type, default_serializers=None):
        if self.serializer:
            serializer = self.serializer
        else:
            _mtype, _serializer = self.get_serializer(content_type, 
                                                      default_serializers)
            serializer = _serializer()
        response = webob.Response()
        try:
            response.status_int = self.code
        except Exception as ex:
            print ex
        if self._headers: 
            for hdr, value in self._headers.items():
                response.headers[hdr] = value
        response.headers['Content-Type'] = content_type
        if self.obj is not None:
            try:
                response.body = serializer.serialize(self.obj)
            except Exception as ex:
                print ex
        return response
    
    @property
    def code(self):
        return self._code or self.default_code
    
    @property
    def headers(self):
        return self._headers.copy()


def action_peek_json(body):
    try:
        decoded = json.loads(body)
    except ValueError:
        msg = "cannot understand JSON"
        raise exception.RequestBodyError(reason=msg)
    if len(decoded) != 1:
        msg = "too many body keys"
        raise exception.RequestBodyError(reason=msg)
    return decoded.keys()[0]


def serializers(**serializers):
    
    def decorator(func):
        if not hasattr(func, 'wsgi_serializers'):
            func.wsgi_serializers = {}
        func.wsgi_serializers.update(serializers)
        return func
    return decorator

def deserializers(**deserializers):
    
    def decorator(func):
        if not hasattr(func, 'wsgi_deserializers'):
            func.wsgi_deserializers = {}
        func.wsgi_deserializers.update(deserializers)
        return func
    
    return decorator


class Resource(base_wsgi.Application):
    
    def __init__(self, controller, action_peek=None, inherits=None,
                 **deserializers):
        self.controller = controller
        default_deserializers = dict(xml=XMLDeserializer,
                                json=JSONDeserializer)
        default_deserializers.update(deserializers)
        self.default_deserializers = default_deserializers
        self.default_serializers = dict(xml=XMLDictSerializer,
                                     json=JSONDictSerializer)
        self.action_peek = dict(json=action_peek_json)
        self.action_peek.update(action_peek or {})
        self.wsgi_actions = {}
        if controller:
            self.register_actions(controller)
    
    def register_actions(self, controller):
        actions = getattr(controller, 'wsgi_actions', {})
        for key, method_name in actions.items():
            self.wsgi_actions[key] = getattr(controller, method_name)
        
    def get_actions_args(self, request_environment):
        if hasattr(self.controller, 'get_action_args'):
            return self.controller.get_action_args(request_environment)
        
        try:
            args = request_environment['wsgiorg.routing_args'][1].copy()
        except(KeyError, IndexError, AttributeError):
            return {}
        
        try:
            del args['controller']
        except KeyError:
            pass
        
        try:
            del args['format']
        except KeyError:
            pass
        
        return args
    
    def get_body(self, request):
        try:
            content_type = request.get_content_type()
        except Exception as ex: 
            print ex
        if not content_type:
            return None, ''
        if len(request.body) <= 0:
            return None, ''
        
        return content_type, request.body
    
    def deserialize(self, meth, content_type, body):
        meth_deserializers = getattr(meth, 'wsgi_deserializers', {})
        try:
            mtype = _MEDIA_TYPE_MAP.get(content_type, content_type)
            if mtype in meth_deserializers:
                deserializer = meth_deserializers[mtype]
            else:
                deserializer = self.default_deserializers[mtype]
        except (KeyError, TypeError):
            #raise exception.InvalidContentType(content_type=content_type)
            pass
        return deserializer().deserialize(body)
    
    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, request):
        print "enter resource call"
        action_args = self.get_actions_args(request.environ)
        action = action_args.pop('action', None)
        content_type, body = self.get_body(request)
        accept = "application/json"
        print "enter resource call"
        try:
            return self._process_stack(request, action, action_args, 
                            content_type, body, accept)
        except Exception as e:
            print e, "###########################3"
            
    
    def _process_stack(self, request, action, action_args,
                       content_type, body, accept):
        try:
            meth = self.get_method(request, action, 
                                   content_type, body)
        except Exception as e:
            print e
            pass
        if body:
            pass
        try:
            if content_type:
                contents = self.deserialize(meth, content_type, body)
            else:
                contents = {}
        except Exception as e:
            print e
            pass
        action_args.update(contents)
#         project_id=action_args.pop("project_id", None)
        context = request.environ.get("glance.context")
#         if(context and project_id and (project_id != context.project_id)):
#             msg = "Malformed request url"
#             return Fault(webob.exc.HTTPBadRequest(explanation=msg))
        response = None
        try:
            action_result = self.dispatch(meth, request, action_args)
        except Exception as e:
            response = e
        if not response:
            resp_obj = None
            if type(action_result) is dict or action_result is None:
                resp_obj = ResponseObject(action_result)
            elif isinstance(action_result, ResponseObject):
                resp_obj = action_result
            else:
                response = action_result
            if resp_obj:
                serializers = getattr(meth, 'wsgi_serializers', {})
                resp_obj._bind_method_serializers(serializers)
                if hasattr(meth, 'wsgi_code'):
                    resp_obj._default_code = meth.wsgi_code
                try:
                    resp_obj.preserializer(accept, self.default_serializers)
                except Exception as ex:
                    print ex
            if resp_obj and not response:
                response = resp_obj.serialize(request, accept,
                        self.default_serializers)
        return response

    def pre_process_extentsions(self, extentsions, request, action_args):
        post = []
        for ext in extentsions:
            if inspect.isgeneratorfunction(ext):
                response = None
                try:
                    gen = ext(req=request, **action_args)
                    response = gen.next()
                except Fault as ex:
                    response = ex
                if response:
                    return response, []
                post.append[gen]
            else:
                post.append(ext)
            return None, reversed(post)
    
    def post_process_extentions(self, extentsions, resp_obj, request,
                action_args):
        for ext in extentsions:
            response = None
            if inspect.isgenerator(ext):
                try:
                    response = ext.send(resp_obj)
                except StopIteration:
                    continue
                except Fault as ex:
                    response = ex
            else:
                try:
                    response = ext(req=request, resp_obj=resp_obj,
                            **action_args)
                except Fault as ex:
                    response = ex 
            if response:
                return response

        return None


    def _set_request_id_header(self, req, headers):
        context = req.environ.get('glance.context')
        if context:
            headers['x-glance-request-id'] = context.request_id
    
    def get_method(self, request, action, content_type, body):
        meth= self._get_method(request, action, content_type, body)
        return meth
    
    def _get_method(self, request, action, content_type, body):
        try:
            if not self.controller:
                meth = getattr(self, action)
            else:
                meth = getattr(self.controller, action)
        except Exception as e:
            print str(e)
            if (not self.wsgi_actions or 
                action not in ['action', 'create', 'delete', 'update', 'show']):
                raise
        else: 
            return meth
        if action == "action":
            mtype = _MEDIA_TYPE_MAP.get(content_type)
            action_name = self.action_peek[mtype](body)
        else:
            action_name = action
        return (self.wsgi_actions[action_name])
        
    def dispatch(self, method, request, action_args):
        result = method(req=request, **action_args)
        return result


def action(name):
    
    def decorator(func):
        func.wsgi_action = name
        return func
    return decorator


class ControllerMetaclass(type):
    
    def __new__(mcs, name, bases, cls_dict): 
        actions = {}
        for base in bases:
            actions.update(getattr(base, 'wsgi_action',{}))
        for key, value in cls_dict.items():
            if not callable(value):
                continue
            if getattr(value, 'wsgi_action', None):
                actions[value.wsgi_action] = key
            cls_dict["wsgi_actions"] = actions
        return super(ControllerMetaclass, mcs).__new__(mcs, name, bases, cls_dict)
        

class Controller(object):
    
    __metaclass__ = ControllerMetaclass
    _view_builder_class = None
    
    def __init__(self, view_builder=None):
        if view_builder:
            self.view_builder = view_builder
        elif self._view_builder_class:
            self.view_builder = self._view_builder_class()
        else:
            self.view_builder = None
    
    @staticmethod
    def is_valid_body(body, entity_name):
        if not (body and entity_name in body):
            return False
        
        def is_dict(d):
            try:
                d.get(None)
                return True
            except:
                return False
            
        if not is_dict(body[entity_name]):
            return False
        return True
        
        
