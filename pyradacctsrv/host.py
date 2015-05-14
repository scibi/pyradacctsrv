#!/usr/bin/env python
# coding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.utils import python_2_unicode_compatible

import re


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


@python_2_unicode_compatible
class Host(object):
    def __init__(self, host_settings, default_settings={}):
        self.settings = {
            'unique_prefix': '',
            'unique_fields': ['NAS-IP-Address', 'Acct-Session-Id']
        }
        self.settings.update(default_settings)
        self.settings.update(host_settings)

        self.secret = self.settings['secret']
        self.filters = []
        try:
            self.filters = self.settings['filters']
        except KeyError:
            pass

    def gen_uniq_id(self, pkt):
        uniqid = "-".join([str(pkt[attr][0]) for attr
                           in self.settings['unique_fields']])
        return self.settings['unique_prefix'] + uniqid

    def filter_max_int(self, pkt, params):
        field_name = params['field_name']
        value = params['value']

        return {k: v for k, v in pkt.iteritems()
                if (k != field_name) or not is_int(v) or (v < value)}

    def filter_extract_regex(self, pkt, params):
        rv = pkt.copy()
        rx = re.compile(params['regex'])
        for k, v in pkt.iteritems():
            if (k == params['field_name']) and isinstance(v, basestring):
                r = rx.match(v)
                if r:
                    rv[params['target']] = r.group(1)
        return rv

    def filter_dict_match(self, pkt, params):
        rv = pkt.copy()
        for k, v in pkt.iteritems():
            if k == params['field_name']:
                try:
                    rv[params['target']] = params['values'][v]
                except KeyError:
                    try:
                        rv[params['target']] = params['default']
                    except KeyError:
                        pass
        return rv

    def apply_filters(self, pkt):
        for f in self.filters:
            filter_fun = getattr(self, 'filter_{}'.format(f['type']), None)
            if filter_fun is None:  # no such filter
                continue
            pkt = filter_fun(pkt, f)
        return pkt
