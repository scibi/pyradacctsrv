#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

import mock
import os
import sys

from twisted.trial import unittest

from pyrad.dictionary import Dictionary
from pyrad.packet import Packet

from pyradacctsrv.packet import AccountigPacket


@python_2_unicode_compatible
class AccountigPacketTest(unittest.TestCase):
    klass = AccountigPacket

    def setUp(self):
        self.data_session_id = 'some-id-1234'
        self.data_src_ip = '2.3.4.5'
        self.path = os.path.join(sys.modules["tests"].__path__[0], 'data')
        self.dictionary = Dictionary(os.path.join(self.path, 'dictionary'))
        self.pkt = Packet(id=0, secret=b'secret',
                          authenticator=b'01234567890ABCDEF',
                          dict=self.dictionary)
        self.pkt[b'Acct-Status-Type'] = 'Start'
        self.pkt[b'Acct-Session-Id'] = self.data_session_id
        self.pkt[b'User-Name'] = 'SomeUser'
        self.pkt.source = (self.data_src_ip, 5000)

    def test_unique_id(self):
        self.pkt[b'NAS-IP-Address'] = '1.2.3.4'
        pkt = self.klass(self.pkt)
        self.assertEqual(
            pkt.uniq_session_id,
            '1.2.3.4-{}'.format(self.data_session_id))

    def test_constructor(self):
        expected_time = 1422464228

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = expected_time

            pkt = self.klass(self.pkt)
            self.assertEqual(
                pkt.uniq_session_id,
                '{}-{}'.format(self.data_src_ip, self.data_session_id))
            self.assertEqual(pkt.status_type, 'Start')
            self.assertEqual(pkt.time_received, expected_time)

    def test_as_dict(self):
        expected_time = 1422464228

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = expected_time

            pkt = self.klass(self.pkt)

            d = pkt.as_dict()

            self.assertEqual(d['Acct-Delay-Time'], 0)
            self.assertEqual(d['Acct-Session-Id'], self.data_session_id)
            self.assertEqual(d['Acct-Session-Time'], 0)
            self.assertEqual(d['Acct-Status-Type'], 'Start')
            self.assertEqual(d['Event-Timestamp'], expected_time)
            self.assertEqual(d['NAS-IP-Address'], self.data_src_ip)
            self.assertEqual(
                d['Unique-Acct-Session-Id'],
                '{}-{}'.format(self.data_src_ip, self.data_session_id))
            self.assertEqual(d['X-Session-Start-Time'], expected_time)
            self.assertEqual(d['X-Session-Stop-Time'], expected_time)
            self.assertEqual(d['User-Name'], 'SomeUser')

    def test_stop_dict(self):
        expected_time = 1422464228
        expected_delay = 10
        expected_session_time = 60

        expected_start_time = (expected_time
                               - expected_delay
                               - expected_session_time)
        expected_stop_time = (expected_time - expected_delay)

        self.pkt[b'Acct-Delay-Time'] = expected_delay
        self.pkt[b'Acct-Session-Time'] = expected_session_time

        with mock.patch('time.time') as time_thing:
            time_thing.return_value = expected_time

            pkt = self.klass(self.pkt)

            d = pkt.as_dict()

            self.assertEqual(d['Event-Timestamp'], expected_time)
            self.assertEqual(d['X-Session-Start-Time'], expected_start_time)
            self.assertEqual(d['X-Session-Stop-Time'], expected_stop_time)
