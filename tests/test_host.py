#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

from twisted.trial import unittest
from mock import MagicMock

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

        self.pkt = {
            'field1': 100,
            'field2': 200,
            'field3': 'some_value',
            'Called-Station-Id': 'AB-CD-EF-11-22-33:some-ssid',
        }

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

        filter_param = {
            'type': 'max_int',
            'field_name': 'field1',
            'value': 150
        }

        rv = self.minimal_host.filter_max_int(self.pkt, filter_param)
        self.assertEqual(rv, self.pkt, msg="field is ok")

        filter_param['field_name'] = 'field2'
        rv = self.minimal_host.filter_max_int(self.pkt, filter_param)
        res = self.pkt.copy()
        res.pop('field2')
        self.assertEqual(rv, res, msg="field is too big")

        filter_param['field_name'] = 'field3'
        rv = self.minimal_host.filter_max_int(self.pkt, filter_param)
        self.assertEqual(rv, self.pkt, msg="field is not integer")

    def test_filter_extract_regex(self):
        res = self.pkt.copy()
        res['SSID-Name'] = 'some-ssid'

        filter_param = {
            'type': 'extract_regexp',
            'field_name': 'Called-Station-Id',
            'regex': '^[^:]*:(.*)',
            'target': 'SSID-Name'
        }

        rv = self.minimal_host.filter_extract_regex(self.pkt, filter_param)
        self.assertEqual(rv, res, msg="field is ok")

        filter_param['field_name'] = 'field1'
        rv = self.minimal_host.filter_extract_regex(self.pkt, filter_param)
        self.assertEqual(rv, self.pkt, msg="field doesn't match")

    def test_filter_dict_match(self):
        res = self.pkt.copy()

        filter_param = {
            'type': 'dict_match',
            'field_name': 'field1',
            'values': {
                100: 'value1',
                'some_value': 200,
            },
            'target': 'destination'
        }

        res['destination'] = 'value1'
        rv = self.minimal_host.filter_dict_match(self.pkt, filter_param)
        self.assertEqual(rv, res, msg="key exists and is an integer")

        res['destination'] = 200
        filter_param['field_name'] = 'field3'
        rv = self.minimal_host.filter_dict_match(self.pkt, filter_param)
        self.assertEqual(rv, res, msg="key exists and is a string")

        filter_param['field_name'] = 'not-existing'
        rv = self.minimal_host.filter_dict_match(self.pkt, filter_param)
        self.assertEqual(rv, self.pkt, msg="field doesn't exist")

        filter_param['field_name'] = 'field2'
        rv = self.minimal_host.filter_dict_match(self.pkt, filter_param)
        self.assertEqual(rv, self.pkt,
                         msg="key doesn't exist and there is no default")

        filter_param['field_name'] = 'field2'
        filter_param['default'] = 'default_value'
        res['destination'] = 'default_value'
        rv = self.minimal_host.filter_dict_match(self.pkt, filter_param)
        self.assertEqual(rv, res,
                         msg="field doesn't exist and there is default")

    def setup_filters(self, filters_conf):
        conf = {
            'address': '10.0.0.1',
            'secret': 'someSecret'
        }
        conf.update(filters_conf)

        h = Host(conf)
        h.filter_max_int = MagicMock(return_value=self.pkt)
        h.filter_extract_regex = MagicMock(return_value=self.pkt)
        h.filter_dict_match = MagicMock(return_value=self.pkt)

        return h

    def test_apply_filters(self):
        conf_max_int = {
            'type': 'max_int',
            'field_name': 'field1',
            'value': 150
        }
        conf_extract_regexp = {
            'type': 'extract_regex',
            'field_name': 'Called-Station-Id',
            'regex': '^[^:]*:(.*)',
            'target': 'SSID-Name'
        }
        conf_dict_match = {
            'type': 'dict_match',
            'field_name': 'field1',
            'values': {
                100: 'value1',
                'abc': 200,
                },
            'target': 'destination'
        }

        h = self.setup_filters(
            {'filters': [conf_max_int, conf_extract_regexp, conf_dict_match]})

        h.apply_filters(self.pkt)

        h.filter_max_int.assert_called_once_with(self.pkt, conf_max_int)
        h.filter_extract_regex.assert_called_once_with(self.pkt,
                                                       conf_extract_regexp)
        h.filter_dict_match.assert_called_once_with(self.pkt, conf_dict_match)

    def test_apply_filters_no_filters(self):
        h = self.setup_filters({})

        h.apply_filters(self.pkt)

        self.assertEqual(h.filter_max_int.called, False)
        self.assertEqual(h.filter_extract_regex.called, False)
        self.assertEqual(h.filter_dict_match.called, False)

    def test_apply_filters_empty_filters(self):
        h = self.setup_filters({'filters': []})

        h.apply_filters(self.pkt)

        self.assertEqual(h.filter_max_int.called, False)
        self.assertEqual(h.filter_extract_regex.called, False)
        self.assertEqual(h.filter_dict_match.called, False)

    def test_apply_filters_chain(self):
        conf = {
            'address': '10.0.0.1',
            'secret': 'someSecret',
            'filters': [
                {
                    'type': 'extract_regex',
                    'field_name': 'Called-Station-Id',
                    'regex': '^[^:]*:(.*)',
                    'target': 'SSID-Name'
                }, {
                    'type': 'dict_match',
                    'field_name': 'SSID-Name',
                    'values': {
                        100: 'value1',
                        'some-ssid': 'yes_it_works',
                        },
                    'target': 'destination'
                }
            ]
        }
        res = self.pkt.copy()
        res['SSID-Name'] = 'some-ssid'
        res['destination'] = 'yes_it_works'

        h = Host(conf)
        rv = h.apply_filters(self.pkt)
        self.assertEqual(rv, res)
