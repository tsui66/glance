#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng



import os
import re

class Error(StandardError):
    code = None
    title = None
    message_format = None
    
    def __init__(self, message=None, **kwargs):
        try:
            message = self._build_message(message, **kwargs)
        except KeyError as e:
            message = self.message_format
        super(Error, self).__init__(message)
    
    def _build_message(self, message, **kwargs):
        if not message:
            message = self.message_format % kwargs
        return message
    
    def __str(self):
        string = super(Error, self).__str__()
        string = re.sub('[ \n]+', ' ', string)
        string = string.strip()
        return string

class ValidationError(Error):
    message_format = "Expecting to find %(attribute)s in %(target)s."\
                       " The server could not comply with the request"\
                       " since it is either malformed or otherwise"\
                       " incorrect. The client is assumed to be in error."
    code = 400
    title = 'Bad Request'

class NotFound(Error):
    message_format = "Could not find %(target)s."
    code = 404
    title = 'Not Found'

class Unauthorized(Error):
    message_format = "The request you have made requires authentication."
    code = 401
    title = 'Not Authorized'

class UnexpectedError(Error):
    message_format = "An unexpected error prevented the server" \
                       " from fulfilling your request. %(exception)s"
    code = 500
    title = 'Internal Server Error'
    
class RequestBodyError(Error):
    message_format = "The request body occur error because %(reason)s."
    code = 450
    title = "Request Body Error"

class BackendError(Exception):
    """ The storage backend is not working properly """

class ImproperlyConfigured(Exception):
    """ Amon is improperly configured """ 
