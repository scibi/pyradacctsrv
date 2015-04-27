#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

#import logging

#from twisted.internet import defer, task
#from twisted.python import log

import yaml


@python_2_unicode_compatible
class ConfigError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

@python_2_unicode_compatible
class Config(object):
    def __init__(self, yaml_config):
        try:
            self.config = yaml.safe_load(yaml_config)
        except yaml.parser.ParserError as e:
            raise ConfigError("Unable to parse config file: {}".format(e))

        if self.config is None:
            raise ConfigError("Unable to parse config file")

        if 'hosts' not in self.config:
            raise ConfigError("Unable to finde hosts definitions")

    def hosts(self):
        hosts={}
        for h in self.config['hosts']:
            hosts[h['address']]=h
            if 'secret' not in h:
                hosts[h['address']]['secret'] = self.config['defaults']['secret']

        return hosts

#    @defer.inlineCallbacks
#    def check_old_sessions(self):
#        log.msg('check_old_sessions()', logLevel=logging.DEBUG)
#        try:
#            old_sessions = yield self.session_db.get_old_sessions()
#            log.msg('check_old_sessions() old_sessions={0}'
#                    .format(old_sessions), logLevel=logging.DEBUG)
#            for s in old_sessions:
#                yield self.session_db.process_stopped(s)
#
#        except txredisapi.ConnectionError as e:
#            log.msg('check_old_sessions - connection error {0}'
#                    .format(e), logLevel=logging.WARNING)
