# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from tests.compat import unittest
from tests.integration.route53 import Route53TestCase

from boto.route53.record import ResourceRecordSets


class TestRoute53ResourceRecordSets(Route53TestCase):
    def test_add_change(self):
        rrs = ResourceRecordSets(self.conn, self.zone.id)

        created = rrs.add_change("CREATE", "vpn.%s." % self.base_domain, "A")
        created.add_value('192.168.0.25')
        rrs.commit()

        rrs = ResourceRecordSets(self.conn, self.zone.id)
        deleted = rrs.add_change('DELETE', "vpn.%s." % self.base_domain, "A")
        deleted.add_value('192.168.0.25')
        rrs.commit()

    def test_record_count(self):
        rrs = ResourceRecordSets(self.conn, self.zone.id)
        hosts = 101

        for hostid in range(hosts):
            rec = "test" + str(hostid) + ".%s" % self.base_domain
            created = rrs.add_change("CREATE", rec, "A")
            ip = '192.168.0.' + str(hostid)
            created.add_value(ip)

            # Max 100 changes per commit
            if (hostid + 1) % 100 == 0:
                rrs.commit()
                rrs = ResourceRecordSets(self.conn, self.zone.id)

        rrs.commit()

        all_records = self.conn.get_all_rrsets(self.zone.id)

        # First time around was always fine
        i = 0
        for rset in all_records:
            i += 1

        # Second time was a failure
        i = 0
        for rset in all_records:
            i += 1

        # Cleanup indivual records
        rrs = ResourceRecordSets(self.conn, self.zone.id)
        for hostid in range(hosts):
            rec = "test" + str(hostid) + ".%s" % self.base_domain
            deleted = rrs.add_change("DELETE", rec, "A")
            ip = '192.168.0.' + str(hostid)
            deleted.add_value(ip)

            # Max 100 changes per commit
            if (hostid + 1) % 100 == 0:
                rrs.commit()
                rrs = ResourceRecordSets(self.conn, self.zone.id)

        rrs.commit()

        # 2nd count should match the number of hosts plus NS/SOA records
        records = hosts + 2
        self.assertEqual(i, records)

if __name__ == '__main__':
    unittest.main()
