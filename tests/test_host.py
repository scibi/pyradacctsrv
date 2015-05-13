#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

from twisted.trial import unittest

from pyradacctsrv.host import Host


@python_2_unicode_compatible
class HostTest(unittest.TestCase):
    def setUp(self):
        self.minimal_host = Host({
            'address': '10.0.0.1',
            'secret': 'someSecret'})

        self.minimal_host_def = Host(
            {'address': '10.0.0.1'},
            default_settings={'secret': 'someSecret'})

    def test_no_address(self):
        self.assertRaises(KeyError, Host, {})

    def test_secret(self):
        self.assertEqual(self.minimal_host.secret, 'someSecret')
        self.assertEqual(self.minimal_host_def.secret, 'someSecret')

    def test_override_secret(self):
        h = Host({'address': '10.0.0.1', 'secret': 'someOtherSecret'},
                 default_settings={'secret': 'someSecret'})
        self.assertEqual(h.secret, 'someOtherSecret')

    def test_gen_uniq_id(self):
        pkt = {
            'Acct-Session-Id': ['Some-session-id'],
            'NAS-IP-Address': ['10.1.1.1'],
            'Acct-Multi-Session-Id': ['other-session-id'],
            'Some-Field': [123]
        }

        self.assertEqual(
            self.minimal_host.gen_uniq_id(pkt),
            '10.1.1.1-Some-session-id',
            msg='default prefix and field list')

        h = Host({'address': '10.0.0.1', 'unique_prefix': 'PREFIX-'},
                 default_settings={'secret': 'someSecret'})
        self.assertEqual(
            h.gen_uniq_id(pkt),
            'PREFIX-10.1.1.1-Some-session-id',
            msg='custom prefix and default filed list')

        h = Host({'address': '10.0.0.1', 'unique_prefix': 'PREF+',
                 'unique_fields': ['Acct-Multi-Session-Id', 'Some-Field']},
                 default_settings={'secret': 'someSecret'})

        self.assertEqual(
            h.gen_uniq_id(pkt),
            'PREF+other-session-id-123',
            msg='custom prefix and field list')

    def test_filter_max_int(self):
        pkt = {
            'field1': 100,
            'field2': 200,
            'field3': 'some_value'
        }

        filter_param = {
            'type': 'max_int',
            'field_name': 'field1',
            'value': 150
        }

        rv = self.minimal_host.filter_max_int(pkt, filter_param)
        self.assertEqual(rv, pkt, msg="field is ok")

        filter_param['field_name'] = 'field2'
        rv = self.minimal_host.filter_max_int(pkt, filter_param)
        res = {'field1': 100, 'field3': 'some_value'}
        self.assertEqual(rv, res, msg="field is too big")

        filter_param['field_name'] = 'field3'
        rv = self.minimal_host.filter_max_int(pkt, filter_param)
        self.assertEqual(rv, pkt, msg="field is not integer")

    def test_filter_extract_regex(self):
        pkt = {
            'field1': 100,
            'Called-Station-Id': 'AB-CD-EF-11-22-33:some-ssid'
        }
        res = pkt.copy()
        res['SSID-Name'] = 'some-ssid'

        filter_param = {
            'type': 'extract_regexp',
            'field_name': 'Called-Station-Id',
            'regex': '^[^:]*:(.*)',
            'target': 'SSID-Name'
        }

        rv = self.minimal_host.filter_extract_regex(pkt, filter_param)
        self.assertEqual(rv, res, msg="field is ok")

        filter_param['field_name'] = 'field1'
        rv = self.minimal_host.filter_extract_regex(pkt, filter_param)
        self.assertEqual(rv, pkt, msg="field doesn't match")

    def test_filter_dict_match(self):
        pkt = {
            'field1': 100,
            'field2': 'abc',
            'field3': 'def'
        }
        res = pkt.copy()
        res['destination'] = 'value1'

        filter_param = {
            'type': 'dict_match',
            'field_name': 'field1',
            'values': {
                100: 'value1',
                'abc': 200,
            },
            'target': 'destination'
        }

        rv = self.minimal_host.filter_dict_match(pkt, filter_param)
        self.assertEqual(rv, res, msg="field exists and is an integer")

        res['destination'] = 200
        filter_param['field_name'] = 'field2'
        rv = self.minimal_host.filter_dict_match(pkt, filter_param)
        self.assertEqual(rv, res, msg="field exists and is a string")

        filter_param['field_name'] = 'field3'
        rv = self.minimal_host.filter_dict_match(pkt, filter_param)
        self.assertEqual(rv, pkt,
                         msg="field doesn't exist and there is no default")

        filter_param['field_name'] = 'field3'
        filter_param['default'] = 'default_value'
        res['destination'] = 'default_value'
        rv = self.minimal_host.filter_dict_match(pkt, filter_param)
        self.assertEqual(rv, res,
                         msg="field doesn't exist and there is default")
