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

import boto
from boto.route53.domains.exceptions import InvalidInput
from tests.compat import unittest


class TestRoute53Domains(unittest.TestCase):
    def setUp(self):
        self.route53domains = boto.connect_route53domains()

    def test_check_domain_availability(self):
        response = self.route53domains.check_domain_availability(
            domain_name='amazon.com',
            idn_lang_code='eng'
        )
        self.assertEqual(response, {'Availability': 'UNAVAILABLE'})

    def test_handle_invalid_input_error(self):
        with self.assertRaises(InvalidInput):
            # Note the invalid character in the domain name.
            self.route53domains.check_domain_availability(
                domain_name='!amazon.com',
            )
