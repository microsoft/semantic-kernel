# Copyright (c) 2015 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.configservice.exceptions import NoSuchConfigurationRecorderException
from tests.compat import unittest


class TestConfigService(unittest.TestCase):
    def setUp(self):
        self.configservice = boto.connect_configservice()

    def test_describe_configuration_recorders(self):
        response = self.configservice.describe_configuration_recorders()
        self.assertIn('ConfigurationRecorders', response)

    def test_handle_no_such_configuration_recorder(self):
        with self.assertRaises(NoSuchConfigurationRecorderException):
            self.configservice.describe_configuration_recorders(
                configuration_recorder_names=['non-existant-recorder'])

    def test_connect_to_non_us_east_1(self):
        self.configservice = boto.configservice.connect_to_region('us-west-2')
        response = self.configservice.describe_configuration_recorders()
        self.assertIn('ConfigurationRecorders', response)
