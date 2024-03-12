# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
# All rights reserved.
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

"""
Tests for Layer1 of Cloudsearch
"""
import time

from tests.unit import unittest
from boto.cloudsearch.layer1 import Layer1
from boto.cloudsearch.layer2 import Layer2
from boto.regioninfo import RegionInfo


class CloudSearchLayer1Test(unittest.TestCase):
    cloudsearch = True

    def setUp(self):
        super(CloudSearchLayer1Test, self).setUp()
        self.layer1 = Layer1()
        self.domain_name = 'test-%d' % int(time.time())

    def test_create_domain(self):
        resp = self.layer1.create_domain(self.domain_name)
        self.addCleanup(self.layer1.delete_domain, self.domain_name)
        self.assertTrue(resp.get('created', False))


class CloudSearchLayer2Test(unittest.TestCase):
    cloudsearch = True

    def setUp(self):
        super(CloudSearchLayer2Test, self).setUp()
        self.layer2 = Layer2()
        self.domain_name = 'test-%d' % int(time.time())

    def test_create_domain(self):
        domain = self.layer2.create_domain(self.domain_name)
        self.addCleanup(domain.delete)
        self.assertTrue(domain.created, False)
        self.assertEqual(domain.domain_name, self.domain_name)
        self.assertEqual(domain.num_searchable_docs, 0)

    def test_initialization_regression(self):
        us_west_2 = RegionInfo(
            name='us-west-2',
            endpoint='cloudsearch.us-west-2.amazonaws.com'
        )
        self.layer2 = Layer2(
            region=us_west_2,
            host='cloudsearch.us-west-2.amazonaws.com'
        )
        self.assertEqual(
            self.layer2.layer1.host,
            'cloudsearch.us-west-2.amazonaws.com'
        )
