#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4

#Created on 2013-8-17
#Copyright 2013 nuoqingyun xuqifeng



import logging
import logging.handlers
import os
import sys 
import stat
import inspect


from oslo.config import cfg

log_opts = [
        cfg.BoolOpt('use_syslog',
            default = 'False',
            help=""),
        cfg.BoolOpt('debug',
            default=False,
            help=""),
        cfg.BoolOpt('verbose',
            default=True,
            help=""),
        cfg.BoolOpt('use_stderr',
            default='False',
            help=""),
        cfg.StrOpt('logfile_mode',
            default='0644',
            help="the default log file mode"),
        cfg.StrOpt('log_file',
            default='/var/log/glance.log',
            help = ""),
        cfg.StrOpt('log_date_format',
            default='%Y-%m-%d %H:%M:%S',
            help=''),
        cfg.StrOpt('log_format',
            default='%(asctime)s %(levelname)8s [%(name)s] %(message)s',
            help=''),
        cfg.ListOpt('default_log_levels',
            default=[
                'amqplib=WARN',
                'sqlalchemy=WARN',
                'suds=INFO'
                'eventlet.wsgi.server=WARN'
                ],
            help='list of logger pairs'),
        cfg.StrOpt('syslog_log_facility',
            default='LOG_USER',
            help='syslog facility to receive log lines'),
        cfg.StrOpt('log-dir',
            default='',
            help=''),

        
        ]

CONF = cfg.CONF
CONF.register_opts(log_opts)

_loggers = {}


class ColorHandler(logging.StreamHandler):
    LEVEL_COLORS = {
        logging.DEBUG: '\033[00;32m',
        logging.INFO: '\033[00;36m',
    #    logging.AUDIT: '\033[01:36m',
        logging.WARN: '\033[01;33m',
        logging.ERROR: '\033[01;31m',
        logging.CRITICAL: '\033[01;31m',
    }
    def format(self, record):
        record.color = self.LEVEL_COLORS[record.levelno]
        return logging.StreamHandler.format(self, record)


class LegacyFormatter(logging.Formatter):

    def format(self, record):
        self._fmt = CONF.logging_default_format_string

        if (record.levelno == logging.DEBUG and
            CONF.logging_debug_format_stuffix):
            self._fmt


class ContextAdapter(logging.LoggerAdapter):

    def __init__(self, logger, project_name, version):
        self.logger = logger
        self.project = project_name
        self.version = version

    @property
    def handlers(self):
        return self.logger.handlers

    def audit(self, msg, *args, **kwargs):
        self.log(logging.AUDIR, msg, *args, **kwargs)

    def deprecated(self, msg, *args, **kwargs):
        pass

    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        extra = kwargs['extra']
        extra.update({'sitename': self.project})
        extra.update({'project':self.project})
        extra.update({'version': self.version})
        extra['extra'] = extra.copy()
        return msg, kwargs
    
    
def _setup_logging_from_conf(product_name):
    log_root = getLogger(None).logger
    for handler in log_root.handlers:
        log_root.removeHandler(handler)
    if CONF.use_syslog:
       facility = _find_facility_from_conf()
       syslog = logging.handlers.SysLogHandler(address='/dev/log',
                    facility=facility)
       log_root.addHandler(syslog)
    log_path = _get_log_file_path()
    if log_path:
        filelog = logging.handlers.WatchedFileHandler(log_path)
        log_root.addHandler(filelog)
        mode = int(CONF.logfile_mode, 8)
        st = os.stat(log_path)
        if st.st_mode != (stat.S_IFREG| mode):
            os.chmod(log_path, mode)
    if CONF.use_stderr:
        streamlog = ColorHandler()
        log_root.addHandler(streamlog)
    elif not CONF.log_file:
        streamlog = logging.StreamHandler(sys.stdout)
        log_root.addHandler(streamlog)
        
    for handler in log_root.handlers:
        dateformat = CONF.log_date_format
        if CONF.log_format:
            handler.setFormatter(logging.Formatter(fmt=CONF.log_format,
                                    datefmt = dateformat))
        #handler.setFormatter()
        if CONF.debug:
            log_root.setLevel(logging.DEBUG)
        elif CONF.verbose:
            log_root.setLevel(logging.INFO)
        else:
            log_root.setLevel(logging.WARNING)

        level = logging.NOTSET
        for pair in CONF.default_log_levels:
            mode, _set, level_name = pair.partition('=')
            level = logging.getLevelName(level_name)
            logger = logging.getLogger(mode)
            logger.setLevel(level)
            for handler in log_root.handlers:
                logger.addHandler(handler)



def setup(product_name):
    _setup_logging_from_conf(product_name)


def _find_facility_from_conf():
    facility_names = logging.handlers.SysLogHandler.facility_names
    facility = getattr(logging.handlers.SysLogHandler,
                        CONF.syslog_log_facility,
                        None)
    if facility is None and CONF.syslog_log_facility in facility_names:
        facility = facility_names.get(CONF.syslog_log_facility)
    return facility


def _get_binary_name():
    return os.path.basename(inspect.stack()[-1][1])


def _get_log_file_path(binary=None):
    logfile = CONF.log_file
    logdir = CONF.log_dir

    if logfile and not logdir:
        return logfile
    if logfile and logdir:
        return os.path.join(logdir, logfile)
    if logdir:
        binary = binary or _get_binary_name()
        return '%s.log' % (os.path.join(logdir, binary))


def getLogger(name='unknown', version='unknown'):
    print _loggers
    if name not in _loggers:
        _loggers[name] = ContextAdapter(logging.getLogger(name),
                name, version)
    return _loggers[name]


if __name__ == "__main__":
    setup("glance")
    log = getLogger("test")
    print log.logger.handlers
    log.warning("this is a test logging method")
