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
    def __init__(self, redis, session_timeout=60, removed_timeout=60):
        self.redis = redis
        self.time_out = session_timeout
        self.removed_timeout = removed_timeout

    def update_last_seen(self, session_id):
        log.msg('SessionDB.update_last_seen({0})'.format(session_id),
                logLevel=logging.DEBUG)
        self.redis.zadd('last_seen', int(time.time()), session_id)

    @defer.inlineCallbacks
    def get_old_sessions(self):
        end_time = int(time.time())-self.time_out
        log.msg('SessionDB.get_old_sessions start=0 end={0}'.format(end_time),
                logLevel=logging.DEBUG)
        rv = yield self.redis.zrangebyscore('last_seen', min=0, max=end_time)
        defer.returnValue(rv)

    @defer.inlineCallbacks
    def get_old_removed(self):
        end_time = int(time.time())-self.removed_timeout
        log.msg('SessionDB.get_old_sessions start=0 end={0}'.format(end_time),
                logLevel=logging.DEBUG)
        rv = yield self.redis.zrangebyscore('recently_removed', min=0, max=end_time)
        defer.returnValue(rv)

    @defer.inlineCallbacks
    def was_removed(self, session_id):
        rv = yield self.redis.zscore('recently_removed', session_id)
        defer.returnValue(rv is not None)

    @defer.inlineCallbacks
    def process_stopped(self, session_id):
        key = 'SESSION:{0}'.format(session_id)
        rv = yield self.redis.hgetall(key)
        if rv:
            log.msg('process_stopped rv={0}'.format(rv))
            encoded = json.dumps(rv)
            yield self.redis.zadd('recently_removed',
                                  int(time.time()),
                                  session_id)
            yield self.redis.rpush('output_queue', encoded)
            yield self.redis.delete(key)
            log.msg('process_stopped session_id={0}'.format(session_id))
            yield self.redis.zrem('last_seen', session_id)

    @defer.inlineCallbacks
    def save_packet(self, packet):
        attr_no_overwrite = [
            b'X-Session-Start-Time'
        ]
        values_overwrite = {key: packet[key] for key in packet.keys()
                            if key not in attr_no_overwrite}
        values_no_overwrite = {key: packet[key] for key in packet.keys()
                               if key in attr_no_overwrite}
        key = 'SESSION:{}'.format(packet[b'Unique-Acct-Session-Id'])

        log.msg('SessionDB.save_packet overwirte={}'.format(values_overwrite))
        log.msg('SessionDB.save_packet no overwirte={}'.format(
            values_no_overwrite))

        # self.redis.hsetnx klucz pole wartosc - zapis o ile nie istnieje
        # self.redis.hset klucz pole wartosc - zapis zawsze
        # self.redis.hmset klucz slownik - zapis wielu wartosci
        yield self.redis.hmset(key, values_overwrite)
        for (k, v) in values_no_overwrite.iteritems():
            yield self.redis.hsetnx(key, k, v)
        yield self.redis.hincr(key, 'X-Packet-Counter')
