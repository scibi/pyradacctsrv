#!/usr/bin/env python
# coding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.utils import python_2_unicode_compatible

from twisted.python import log
import time


@python_2_unicode_compatible
class AccountigPacket(object):
    def __init__(self, pkt):
        self.pkt = pkt

        try:
            self.nas_ip_addr = pkt[b'NAS-IP-Address'][0]
        except KeyError:
            self.nas_ip_addr = pkt.source[0]
        self.status_type = pkt[b'Acct-Status-Type'][0]
        self.uniq_session_id = '{}-{}'.format(self.nas_ip_addr,
                                              pkt[b'Acct-Session-Id'][0])
        self.time_received = int(time.time())

        if b'NAS-IP-Address' not in pkt:
            log.msg('WARNING: No NAS-IP-Address: {}'.format(self.dump()))

    def __str__(self):
        return '{}: {}'.format(self.uniq_session_id, self.pkt)

    def dump(self):
        attrs = '\n'.join(['\t{}: {}'.format(k, self.pkt[k])
                           for k in self.pkt.keys()])
        attrs += '\n\ttime received: {}'.format(self.time_received)
        return '{}:\n{}'.format(self.uniq_session_id, attrs)

    def as_dict(self):
        d = {
            b'Event-Timestamp': self.time_received,
            b'NAS-IP-Address': self.nas_ip_addr,
            b'Acct-Delay-Time': 0,
            b'Acct-Session-Time': 0,
        }
        for key in self.pkt.keys():
            d[key] = self.pkt[key][0]

        d[b'Unique-Acct-Session-Id'] = self.uniq_session_id
        d[b'X-Session-Start-Time'] = (d[b'Event-Timestamp']
                                      - d[b'Acct-Delay-Time']
                                      - d[b'Acct-Session-Time'])
        d[b'X-Session-Stop-Time'] = (d[b'X-Session-Start-Time']
                                     + d[b'Acct-Session-Time'])
        return d
