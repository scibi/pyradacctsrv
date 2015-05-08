#!/usr/bin/env python
# coding: utf-8

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from twisted.internet import defer
from twisted.python import log
from pyrad import curved

from packet import AccountigPacket


class RADIUSAccountingProtocol(curved.RADIUSAccounting, object):
    def __init__(self, session_db, hosts, rad_dict):
        log.msg('RADIUSAccountingProtocol.__init__() - before super')
        super(RADIUSAccountingProtocol, self).__init__(hosts, rad_dict)
        log.msg('RADIUSAccountingProtocol.__init__() - after super')
        self.session_db = session_db

    @defer.inlineCallbacks
    def processPacket(self, pkt):
        super(RADIUSAccountingProtocol, self).processPacket(pkt)

        if not pkt.VerifyAcctRequest():
            raise curved.PacketError('Authentication failed ')

        p = AccountigPacket(pkt)
        log.msg(p.dump())

        was_removed = yield self.session_db.was_removed(p.uniq_session_id)
        log.msg('{}: Was removed: {}'.format(p.uniq_session_id, was_removed))
        if was_removed:
            raise curved.PacketError('Ignoring removed packet')

        if p.status_type in ('Start', 'Stop', 'Interim-Update'):
            self.session_db.update_last_seen(p.uniq_session_id)
            self.session_db.save_packet(p.as_dict())
            if p.status_type == 'Stop':
                self.processStop(p)
        else:
            raise curved.PacketError(
                'Unknown status type ({})'.format(p.status_type))

        reply = self.createReplyPacket(pkt)
        self.transport.write(reply.ReplyPacket(), reply.source)

    def processStop(self, p):
        log.msg('PKT: processStop')
        self.session_db.process_stopped(p.uniq_session_id)
