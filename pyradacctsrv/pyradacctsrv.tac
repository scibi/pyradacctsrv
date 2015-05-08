from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from twisted.application.service import Application

from service import RAService


application = Application("Python RADIUS Accounting Server")

srv = RAService("/tmp/pyradacct.yml")
srv.setServiceParent(application)
