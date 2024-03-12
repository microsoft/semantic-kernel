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

from boto.exception import JSONResponseError
from boto.opsworks import connect_to_region, regions, RegionInfo
from boto.opsworks.layer1 import OpsWorksConnection
from tests.compat import unittest


class TestOpsWorksConnection(unittest.TestCase):
    opsworks = True

    def setUp(self):
        self.api = OpsWorksConnection()

    def test_describe_stacks(self):
        response = self.api.describe_stacks()
        self.assertIn('Stacks', response)

    def test_validation_errors(self):
        with self.assertRaises(JSONResponseError):
            self.api.create_stack('testbotostack', 'us-east-1',
                                  'badarn', 'badarn2')


class TestOpsWorksHelpers(unittest.TestCase):
    opsworks = True

    def test_regions(self):
        response = regions()
        self.assertIsInstance(response[0], RegionInfo)

    def test_connect_to_region(self):
        connection = connect_to_region('us-east-1')
        self.assertIsInstance(connection, OpsWorksConnection)
