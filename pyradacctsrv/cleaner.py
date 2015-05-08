#!/usr/bin/env python
# coding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.utils import python_2_unicode_compatible

import logging

from twisted.internet import defer, task
from twisted.python import log

import txredisapi


@python_2_unicode_compatible
class SessionCleaner(object):
    def __init__(self, session_db, interval=10):
        self.session_db = session_db
        self.lc = task.LoopingCall(self.check_old_sessions)
        self.lc.start(interval)

    @defer.inlineCallbacks
    def check_old_sessions(self):
        log.msg('check_old_sessions()', logLevel=logging.DEBUG)
        try:
            old_sessions = yield self.session_db.get_old_sessions()
            log.msg('check_old_sessions() old_sessions={0}'
                    .format(old_sessions), logLevel=logging.DEBUG)
            for s in old_sessions:
                yield self.session_db.process_stopped(s)

        except txredisapi.ConnectionError as e:
            log.msg('check_old_sessions - connection error {0}'
                    .format(e), logLevel=logging.WARNING)
