#!/usr/bin/env python
# coding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.utils import python_2_unicode_compatible

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

        self.session_timeout = 900
        self.removed_timeout = 900

        try:
            self.session_timeout = self.config['timeouts']['session']
        except KeyError:
            pass

        try:
            self.removed_timeout = self.config['timeouts']['removed']
        except KeyError:
            pass

    def hosts(self):
        hosts = {}
        default_secret = None
        try:
            default_secret = self.config['defaults']['secret']
        except KeyError:
            pass

        for h in self.config['hosts']:
            hosts[h['address']] = h
            if 'secret' not in h:
                hosts[h['address']]['secret'] = default_secret

        return hosts
