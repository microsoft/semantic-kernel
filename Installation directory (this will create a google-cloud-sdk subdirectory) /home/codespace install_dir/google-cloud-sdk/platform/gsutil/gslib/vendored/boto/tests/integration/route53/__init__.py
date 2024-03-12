# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2014 Tellybug, Matt Millar
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import time
import unittest
from nose.plugins.attrib import attr
from boto.route53.connection import Route53Connection


@attr(route53=True)
class Route53TestCase(unittest.TestCase):
    def setUp(self):
        super(Route53TestCase, self).setUp()
        self.conn = Route53Connection()
        self.base_domain = 'boto-test-%s.com' % str(int(time.time()))
        self.zone = self.conn.create_zone(self.base_domain)

    def tearDown(self):
        self.zone.delete()
        super(Route53TestCase, self).tearDown()
