#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

import mock
import json

from twisted.internet import defer
from twisted.trial import unittest

from pyradacctsrv.sessiondb import SessionDB

from tests.testing import dmockfunc


@python_2_unicode_compatible
class SessionDBTest(unittest.TestCase):
    @mock.patch('txredisapi.lazyConnectionPool')
    def setUp(self, lc):
        self.redis_conn = mock.Mock()
        self.expected_session_timeout = 120
        self.expected_removed_timeout = 600

        self.session_db = SessionDB(
            redis=self.redis_conn,
            session_timeout=self.expected_session_timeout,
            removed_timeout=self.expected_removed_timeout
        )

#        self.tr_process_stopped_calls = []
#
#        def process_stopped_se(session_id):
#            self.tr_process_stopped_calls.append(session_id)
#
#        self.session_db.process_stopped = gen_nondeferred_mock(
#            side_effect=process_stopped_se)
#
#        self.cleaner = SessionCleaner(session_db=self.session_db,
#                                      interval=self.expected_lc_interval)

    def test_update_last_seen_zadd_called(self):
        expected_score = 1422464228

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = expected_score
            self.session_db.update_last_seen('some_id')

        self.redis_conn.zadd.assert_called_with('last_seen',
                                                expected_score,
                                                'some_id')

    @defer.inlineCallbacks
    def test_get_old_sessions_zrangebyscore_called(self):
        simulated_time = 1422464228
        expected_score = simulated_time - self.expected_session_timeout
        expected_sessions = ['a', 'b']

        self.redis_conn.zrangebyscore = dmockfunc(expected_sessions)

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = simulated_time

            rv = yield self.session_db.get_old_sessions()

        self.assertEqual(rv, expected_sessions)
        self.redis_conn.zrangebyscore.assert_called_with('last_seen', min=0,
                                                         max=expected_score)

    @defer.inlineCallbacks
    def test_get_old_removed_sessions_zrangebyscore_called(self):
        simulated_time = 1422464228
        expected_score = simulated_time - self.expected_removed_timeout
        expected_sessions = ['a', 'b']

        self.redis_conn.zrangebyscore = dmockfunc(expected_sessions)

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = simulated_time

            rv = yield self.session_db.get_old_removed()

        self.assertEqual(rv, expected_sessions)
        self.redis_conn.zrangebyscore.assert_called_with('recently_removed', min=0,
                                                         max=expected_score)

    @defer.inlineCallbacks
    def test_was_removed_true(self):
        session_id = 'some_session_id'
        self.redis_conn.zscore = dmockfunc(1234)

        rv = yield self.session_db.was_removed(session_id)

        self.assertEqual(rv, True)
        self.redis_conn.zscore.assert_called_with('recently_removed', session_id)

    @defer.inlineCallbacks
    def test_was_removed_false(self):
        session_id = 'some_session_id'
        self.redis_conn.zscore = dmockfunc(None)

        rv = yield self.session_db.was_removed(session_id)

        self.assertEqual(rv, False)

    @defer.inlineCallbacks
    def test_process_stopped_exisiting(self):
        session_id = 'abc'
        expected_dict = {'a': 'b', 'c': 'd'}
        expected_score = 1422464228

        self.redis_conn.hgetall = dmockfunc(expected_dict)

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = expected_score
            yield self.session_db.process_stopped(session_id)

        self.redis_conn.zadd.assert_called_with('recently_removed',
                                                expected_score,
                                                session_id)
        self.redis_conn.hgetall.assert_called_with('SESSION:{0}'.format(
            session_id))
        self.redis_conn.delete.assert_called_with('SESSION:{0}'.format(
            session_id))
        self.redis_conn.zrem.assert_called_with('last_seen', session_id)
        self.redis_conn.rpush.assert_called_with('output_queue', mock.ANY)
        self.assertEqual(json.loads(self.redis_conn.rpush.call_args[0][1]),
                         expected_dict)

    @defer.inlineCallbacks
    def test_process_stopped_not_exisiting(self):
        session_id = 'abc'

        self.redis_conn.hgetall = dmockfunc({})

        yield self.session_db.process_stopped(session_id)

        self.redis_conn.hgetall.assert_called_with('SESSION:{0}'.format(
            session_id))
        self.assertFalse(self.redis_conn.delete.called,
                         msg='redis.delete should not be called')
        self.assertFalse(self.redis_conn.zrem.called,
                         msg='redis.zrem should not be called')
        self.assertFalse(self.redis_conn.zadd.called,
                         msg='redis.zadd should not be called')
        self.assertFalse(self.redis_conn.rpush.called,
                         msg='redis.rpush should not be called')

    @defer.inlineCallbacks
    def test_save_packet(self):
        session_id = 'some_id'
        no_overwrite = [b'X-Session-Start-Time']
        packet = {
            b'Unique-Acct-Session-Id': session_id,
            b'Acct-Input-Octets': 10,
            b'Acct-Output-Octets': 20,
            b'User-Name': 'user1',
            b'X-Session-Start-Time': 100,
            b'X-Session-Stop-Time': 200,
        }

        session_key = 'SESSION:{}'.format(session_id)
        packet_no_overwrite = {k: v for (k, v) in packet.iteritems()
                               if k not in no_overwrite}

        yield self.session_db.save_packet(packet)

        self.redis_conn.hmset.assert_called_with(session_key,
                                                 packet_no_overwrite)
        self.redis_conn.hsetnx.assert_called_with(session_key,
                                                  b'X-Session-Start-Time', 100)
        self.redis_conn.hincr.assert_called_with(session_key,
                                                 'X-Packet-Counter')
