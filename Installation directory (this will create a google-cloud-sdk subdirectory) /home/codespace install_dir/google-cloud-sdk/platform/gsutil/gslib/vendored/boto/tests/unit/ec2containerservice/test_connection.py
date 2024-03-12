# Copyright (c) 2015 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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
from mock import Mock
from tests.unit import unittest

import boto.ec2containerservice
from boto.ec2containerservice.layer1 import EC2ContainerServiceConnection
from boto.compat import http_client


class TestConnectToRegion(unittest.TestCase):

    def setUp(self):
        self.https_connection = Mock(spec=http_client.HTTPSConnection)
        self.https_connection_factory = (
            Mock(return_value=self.https_connection), ())

    def test_aws_region(self):
        ecs = boto.ec2containerservice.connect_to_region('us-east-1',
            https_connection_factory=self.https_connection_factory,
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key'
        )
        self.assertIsInstance(ecs, EC2ContainerServiceConnection)
