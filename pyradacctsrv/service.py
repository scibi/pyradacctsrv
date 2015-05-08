#!/usr/bin/env python
# coding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from twisted.internet import reactor
from twisted.application import service
from pyrad import server
from pyrad import dictionary
import txredisapi

from cleaner import SessionCleaner
from sessiondb import SessionDB
from config import Config
from protocol import RADIUSAccountingProtocol


class RAService(service.Service):
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = Config(open(self.config_file, 'r'))
        hosts = self.config.hosts()
        self.hosts = {k: server.RemoteHost(v['address'],
                                           v['secret'],
                                           v['name'])
                      for k, v in hosts.items()}

    def startService(self):
        print("startService()")
        self.sdb = SessionDB(redis=txredisapi.lazyConnectionPool())
        self.cleaner = SessionCleaner(session_db=self.sdb)
        self._port = reactor.listenUDP(1813, RADIUSAccountingProtocol(
            session_db=self.sdb,
            hosts=self.hosts,
            rad_dict=dictionary.Dictionary('dictionary')))

    def stopService(self):
        print("stopService()")
        return self._port.stopListening()
