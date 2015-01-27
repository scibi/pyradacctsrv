#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

from mock import patch, Mock

from twisted.internet import defer
from twisted.trial import unittest

import txredisapi
from pyradacctsrv.cleaner import SessionCleaner

from tests.testing import gen_nondeferred_mock, dmockfunc, fmockfunc


@python_2_unicode_compatible
class SessionCleanerTest(unittest.TestCase):
    @patch('twisted.internet.task.LoopingCall')
    def setUp(self, lc):
        self.expected_lc_interval = 5

        self.lc = lc
        self.lc_start = Mock()
        self.lc.return_value = self.lc_start

        self.session_db = Mock()

        self.tr_process_stopped_calls = []

        def process_stopped_se(session_id):
            self.tr_process_stopped_calls.append(session_id)

        self.session_db.process_stopped = gen_nondeferred_mock(
            side_effect=process_stopped_se)

        self.cleaner = SessionCleaner(session_db=self.session_db,
                                      interval=self.expected_lc_interval)

    def test_init_looping_call_scheduled(self):
        self.lc.assert_called_with(self.cleaner.check_old_sessions)

    def test_init_looping_call_started(self):
        self.lc_start.start.assert_called_with(self.expected_lc_interval)

    @defer.inlineCallbacks
    def _test_process_stopped(self, arg):
        self.session_db.get_old_sessions = dmockfunc(arg)
        yield self.cleaner.check_old_sessions()
        self.assertEqual(self.tr_process_stopped_calls, arg)

    def test_check_old_sessions_process_stopped_called(self):
        return self._test_process_stopped(['a', 'b', 'c'])

    def test_check_old_sessions_process_stopped_not_called(self):
        return self._test_process_stopped([])

    @defer.inlineCallbacks
    def test_check_old_sessions_handle_ConnectionError(self):
        self.session_db.get_old_sessions = fmockfunc(
            txredisapi.ConnectionError())
        yield self.cleaner.check_old_sessions()
        self.assertEqual(self.tr_process_stopped_calls, [])

    def test_check_old_sessions_not_handle_other_errors(self):
        self.session_db.get_old_sessions = fmockfunc(
            txredisapi.ResponseError())
        d = self.cleaner.check_old_sessions()
        return self.assertFailure(d, txredisapi.ResponseError)
