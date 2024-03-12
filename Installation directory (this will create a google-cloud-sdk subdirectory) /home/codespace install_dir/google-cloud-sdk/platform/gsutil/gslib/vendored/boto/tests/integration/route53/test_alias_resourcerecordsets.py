# Copyright (c) 2014 Netflix, Inc. Stefan Praszalowicz
# Copyright (c) 2014 42Lines, Inc. Jim Browne
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
from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets
from boto.route53.exception import DNSServerError


class TestRoute53AliasResourceRecordSets(unittest.TestCase):
    route53 = True

    def setUp(self):
        super(TestRoute53AliasResourceRecordSets, self).setUp()
        self.conn = Route53Connection()
        self.base_domain = 'boto-test-%s.com' % str(int(time.time()))
        self.zone = self.conn.create_zone(self.base_domain)
        # a standard record to use as the target for our alias
        self.zone.add_a('target.%s' % self.base_domain, '102.11.23.1')

    def tearDown(self):
        self.zone.delete_a('target.%s' % self.base_domain)
        self.zone.delete()
        super(TestRoute53AliasResourceRecordSets, self).tearDown()

    def test_incomplete_add_alias_failure(self):
        base_record = dict(name="alias.%s." % self.base_domain,
                           type="A",
                           alias_dns_name="target.%s" % self.base_domain,
                           alias_hosted_zone_id=self.zone.id,
                           identifier="boto:TestRoute53AliasResourceRecordSets")

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        rrs.add_change(action="UPSERT", **base_record)

        try:
            self.assertRaises(DNSServerError, rrs.commit)
        except:
            # if the call somehow goes through, delete our unexpected new record before failing test
            rrs = ResourceRecordSets(self.conn, self.zone.id)
            rrs.add_change(action="DELETE", **base_record)
            rrs.commit()
            raise

    def test_add_alias(self):
        base_record = dict(name="alias.%s." % self.base_domain,
                           type="A",
                           alias_evaluate_target_health=False,
                           alias_dns_name="target.%s" % self.base_domain,
                           alias_hosted_zone_id=self.zone.id,
                           identifier="boto:TestRoute53AliasResourceRecordSets")

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        rrs.add_change(action="UPSERT", **base_record)
        rrs.commit()

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        rrs.add_change(action="DELETE", **base_record)
        rrs.commit()

    def test_set_alias(self):
        base_record = dict(name="alias.%s." % self.base_domain,
                           type="A",
                           identifier="boto:TestRoute53AliasResourceRecordSets")

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        new = rrs.add_change(action="UPSERT", **base_record)
        new.set_alias(self.zone.id, "target.%s" % self.base_domain, False)
        rrs.commit()

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        delete = rrs.add_change(action="DELETE", **base_record)
        delete.set_alias(self.zone.id, "target.%s" % self.base_domain, False)
        rrs.commit()

    def test_set_alias_backwards_compatability(self):
        base_record = dict(name="alias.%s." % self.base_domain,
                           type="A",
                           identifier="boto:TestRoute53AliasResourceRecordSets")

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        new = rrs.add_change(action="UPSERT", **base_record)
        new.set_alias(self.zone.id, "target.%s" % self.base_domain)
        rrs.commit()

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        delete = rrs.add_change(action="DELETE", **base_record)
        delete.set_alias(self.zone.id, "target.%s" % self.base_domain)
        rrs.commit()


if __name__ == '__main__':
    unittest.main()
