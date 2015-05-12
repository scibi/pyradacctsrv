#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible

from twisted.trial import unittest

from pyradacctsrv.config import Config, ConfigError


@python_2_unicode_compatible
class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.minimal_config = Config("""
---
hosts:
""")

    def test_empty_config(self):
        self.assertRaises(ConfigError, Config, "---")

    def test_broken_config(self):
        self.assertRaises(ConfigError, Config, "[")

    def test_no_hosts(self):
        self.assertRaises(ConfigError, Config, "defaults:")

    def test_get_hosts(self):
        c = Config("""
---
hosts:
  - address: 10.0.0.1
    secret:  test1
    name:    nas1
  - address: 10.0.0.2
    name:    nas2
    secret:  test1
  - address: 10.0.0.3
    secret:  test1
    name:    nas3
""")
        hosts = c.hosts()

        self.assertEqual(len(hosts), 3)
        for h in hosts.values():
            self.assertIn('address', h)
            self.assertIn('secret', h)
            self.assertIn('name', h)

    def test_default_secret(self):
        c = Config("""
---
defaults:
  secret: sec_def
hosts:
  - address: 10.0.0.1
    secret:  sec_nas1
    name:    nas1
  - address: 10.0.0.2
    name:    nas2
  - address: 10.0.0.3
    name:    nas3
""")
        hosts = c.hosts()
        for h in hosts.values():
            self.assertIn('secret', h)
        self.assertEqual(hosts['10.0.0.1']['secret'], 'sec_nas1')
        self.assertEqual(hosts['10.0.0.2']['secret'], 'sec_def')
        self.assertEqual(hosts['10.0.0.3']['secret'], 'sec_def')

    def test_timeout_defaults(self):
        self.assertEqual(self.minimal_config.session_timeout, 900)
        self.assertEqual(self.minimal_config.removed_timeout, 900)

    def test_timeout_custom(self):
        c = Config("""
---
timeouts:
  session: 60
  removed: 61
hosts:
""")
        self.assertEqual(c.session_timeout, 60)
        self.assertEqual(c.removed_timeout, 61)
