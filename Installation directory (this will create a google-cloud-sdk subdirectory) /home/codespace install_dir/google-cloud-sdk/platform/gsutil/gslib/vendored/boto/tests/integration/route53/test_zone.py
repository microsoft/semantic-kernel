# Copyright (c) 2011 Blue Pines Technologies LLC, Brad Carleton
# www.bluepines.org
# Copyright (c) 2012 42 Lines Inc., Jim Browne
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
#

import time
from tests.compat import unittest
from nose.plugins.attrib import attr
from boto.route53.connection import Route53Connection
from boto.exception import TooManyRecordsException
from boto.vpc import VPCConnection


@attr(route53=True)
class TestRoute53Zone(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        route53 = Route53Connection()
        self.base_domain = 'boto-test-%s.com' % str(int(time.time()))
        zone = route53.get_zone(self.base_domain)
        if zone is not None:
            zone.delete()
        self.zone = route53.create_zone(self.base_domain)

    def test_nameservers(self):
        self.zone.get_nameservers()

    def test_a(self):
        self.zone.add_a(self.base_domain, '102.11.23.1', 80)
        record = self.zone.get_a(self.base_domain)
        self.assertEquals(record.name, u'%s.' % self.base_domain)
        self.assertEquals(record.resource_records, [u'102.11.23.1'])
        self.assertEquals(record.ttl, u'80')
        self.zone.update_a(self.base_domain, '186.143.32.2', '800')
        record = self.zone.get_a(self.base_domain)
        self.assertEquals(record.name, u'%s.' % self.base_domain)
        self.assertEquals(record.resource_records, [u'186.143.32.2'])
        self.assertEquals(record.ttl, u'800')

    def test_cname(self):
        self.zone.add_cname(
            'www.%s' % self.base_domain,
            'webserver.%s' % self.base_domain,
            200
        )
        record = self.zone.get_cname('www.%s' % self.base_domain)
        self.assertEquals(record.name, u'www.%s.' % self.base_domain)
        self.assertEquals(record.resource_records, [
            u'webserver.%s.' % self.base_domain
        ])
        self.assertEquals(record.ttl, u'200')
        self.zone.update_cname(
            'www.%s' % self.base_domain,
            'web.%s' % self.base_domain,
            45
        )
        record = self.zone.get_cname('www.%s' % self.base_domain)
        self.assertEquals(record.name, u'www.%s.' % self.base_domain)
        self.assertEquals(record.resource_records, [
            u'web.%s.' % self.base_domain
        ])
        self.assertEquals(record.ttl, u'45')

    def test_mx(self):
        self.zone.add_mx(
            self.base_domain,
            [
                '10 mx1.%s' % self.base_domain,
                '20 mx2.%s' % self.base_domain,
            ],
            1000
        )
        record = self.zone.get_mx(self.base_domain)
        self.assertEquals(set(record.resource_records),
                          set([u'10 mx1.%s.' % self.base_domain,
                               u'20 mx2.%s.' % self.base_domain]))
        self.assertEquals(record.ttl, u'1000')
        self.zone.update_mx(
            self.base_domain,
            [
                '10 mail1.%s' % self.base_domain,
                '20 mail2.%s' % self.base_domain,
            ],
            50
        )
        record = self.zone.get_mx(self.base_domain)
        self.assertEquals(set(record.resource_records),
                          set([u'10 mail1.%s.' % self.base_domain,
                               '20 mail2.%s.' % self.base_domain]))
        self.assertEquals(record.ttl, u'50')

    def test_get_records(self):
        self.zone.get_records()

    def test_get_nameservers(self):
        self.zone.get_nameservers()

    def test_get_zones(self):
        route53 = Route53Connection()
        route53.get_zones()

    def test_identifiers_wrrs(self):
        self.zone.add_a('wrr.%s' % self.base_domain, '1.2.3.4',
                        identifier=('foo', '20'))
        self.zone.add_a('wrr.%s' % self.base_domain, '5.6.7.8',
                        identifier=('bar', '10'))
        wrrs = self.zone.find_records(
            'wrr.%s' % self.base_domain,
            'A',
            all=True
        )
        self.assertEquals(len(wrrs), 2)
        self.zone.delete_a('wrr.%s' % self.base_domain, all=True)

    def test_identifiers_lbrs(self):
        self.zone.add_a('lbr.%s' % self.base_domain, '4.3.2.1',
                        identifier=('baz', 'us-east-1'))
        self.zone.add_a('lbr.%s' % self.base_domain, '8.7.6.5',
                        identifier=('bam', 'us-west-1'))
        lbrs = self.zone.find_records(
            'lbr.%s' % self.base_domain,
            'A',
            all=True
        )
        self.assertEquals(len(lbrs), 2)
        self.zone.delete_a('lbr.%s' % self.base_domain,
                           identifier=('bam', 'us-west-1'))
        self.zone.delete_a('lbr.%s' % self.base_domain,
                           identifier=('baz', 'us-east-1'))

    def test_toomany_exception(self):
        self.zone.add_a('exception.%s' % self.base_domain, '4.3.2.1',
                        identifier=('baz', 'us-east-1'))
        self.zone.add_a('exception.%s' % self.base_domain, '8.7.6.5',
                        identifier=('bam', 'us-west-1'))
        self.assertRaises(TooManyRecordsException,
                          lambda: self.zone.get_a('exception.%s' %
                                                  self.base_domain))
        self.zone.delete_a('exception.%s' % self.base_domain, all=True)

    @classmethod
    def tearDownClass(self):
        self.zone.delete_a(self.base_domain)
        self.zone.delete_cname('www.%s' % self.base_domain)
        self.zone.delete_mx(self.base_domain)
        self.zone.delete()


@attr(route53=True)
class TestRoute53PrivateZone(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        time_str = str(int(time.time()))
        self.route53 = Route53Connection()
        self.base_domain = 'boto-private-zone-test-%s.com' % time_str
        self.vpc = VPCConnection()
        self.test_vpc = self.vpc.create_vpc(cidr_block='10.11.0.0/16')
        # tag the vpc to make it easily identifiable if things go spang
        self.test_vpc.add_tag("Name", self.base_domain)
        self.zone = self.route53.get_zone(self.base_domain)
        if self.zone is not None:
            self.zone.delete()

    def test_create_private_zone(self):
        self.zone = self.route53.create_hosted_zone(self.base_domain,
                                                    private_zone=True,
                                                    vpc_id=self.test_vpc.id,
                                                    vpc_region='us-east-1')

    @classmethod
    def tearDownClass(self):
        if self.zone is not None:
            self.zone.delete()
        self.test_vpc.delete()

if __name__ == '__main__':
    unittest.main(verbosity=3)
