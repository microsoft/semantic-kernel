#!/usr/bin/env python
# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.route53.zone import Zone
from tests.compat import mock, unittest


class TestZone(unittest.TestCase):
    def test_find_records(self):
        mock_connection = mock.Mock()
        zone = Zone(mock_connection, {})
        zone.id = None
        rr_names = ['amazon.com', 'amazon.com', 'aws.amazon.com',
                    'aws.amazon.com']
        mock_rrs = []
        # Create some mock resource records.
        for rr_name in rr_names:
            mock_rr = mock.Mock()
            mock_rr.name = rr_name
            mock_rr.type = 'A'
            mock_rr.weight = None
            mock_rr.region = None
            mock_rrs.append(mock_rr)

        # Set the last resource record to ``None``. The ``find_records`` loop
        # should never hit this.
        mock_rrs[3] = None

        mock_connection.get_all_rrsets.return_value = mock_rrs
        mock_connection._make_qualified.return_value = 'amazon.com'

        # Ensure that the ``None`` type object was not iterated over.
        try:
            result_rrs = zone.find_records('amazon.com', 'A', all=True)
        except AttributeError as e:
            self.fail("find_records() iterated too far into resource"
                      " record list.")

        # Determine that the resulting records are correct.
        self.assertEqual(result_rrs, [mock_rrs[0], mock_rrs[1]])


if __name__ == "__main__":
    unittest.main()
