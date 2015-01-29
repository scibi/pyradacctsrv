#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

from twisted.internet import defer
from twisted.python import log
import time
import json
import logging


@python_2_unicode_compatible
class SessionDB(object):
    def __init__(self, redis, session_timeout=60):
        self.redis = redis
        self.time_out = session_timeout

    def update_last_seen(self, session_id):
        log.msg('SessionDB.update_last_seen({})'.format(session_id),
                logLevel=logging.DEBUG)
        self.redis.zadd('last_seen', int(time.time()), session_id)

    @defer.inlineCallbacks
    def get_old_sessions(self):
        end_time = int(time.time())-self.time_out
        log.msg('SessionDB.get_old_sessions start=0 end={}'.format(end_time),
                logLevel=logging.DEBUG)
        rv = yield self.redis.zrangebyscore('last_seen', min=0, max=end_time)
        defer.returnValue(rv)

    @defer.inlineCallbacks
    def process_stopped(self, session_id):
        key = 'SESSION:{}'.format(session_id)
        rv = yield self.redis.hgetall(key)
        if rv:
            log.msg('process_stopped rv={}'.format(rv))
            encoded = json.dumps(rv)
            yield self.redis.rpush('output_queue', encoded)
            yield self.redis.delete(key)
            log.msg('process_stopped session_id={}'.format(session_id))
            yield self.redis.zrem('last_seen', session_id)
