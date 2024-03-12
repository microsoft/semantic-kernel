# -*- coding: utf-8 -*-

# Copyright (c) 2014 Steven Richards <sbrichards@mit.edu>
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
Unit test for passing in 'host' parameter and overriding the region
See issue: #2522
"""
from tests.compat import unittest

from boto.s3.connection import S3Connection
from boto.s3 import connect_to_region

class S3SpecifyHost(unittest.TestCase):
    s3 = True

    def testWithNonAWSHost(self):
        connect_args = dict({'host':'www.not-a-website.com'})
        connection = connect_to_region('us-east-1', **connect_args)
        self.assertEquals('www.not-a-website.com', connection.host)
        self.assertIsInstance(connection, S3Connection)

    def testSuccessWithHostOverrideRegion(self):
        connect_args = dict({'host':'s3.amazonaws.com'})
        connection = connect_to_region('us-west-2', **connect_args)
        self.assertEquals('s3.amazonaws.com', connection.host)
        self.assertIsInstance(connection, S3Connection)


    def testSuccessWithDefaultUSWest1(self):
        connection = connect_to_region('us-west-2')
        self.assertEquals('s3-us-west-2.amazonaws.com', connection.host)
        self.assertIsInstance(connection, S3Connection)

    def testSuccessWithDefaultUSEast1(self):
        connection = connect_to_region('us-east-1')
        self.assertEquals('s3.amazonaws.com', connection.host)
        self.assertIsInstance(connection, S3Connection)

    def testSuccessWithDefaultEUCentral1(self):
        connection = connect_to_region('eu-central-1')
        self.assertEquals('s3.eu-central-1.amazonaws.com', connection.host)
        self.assertIsInstance(connection, S3Connection)

    def testDefaultWithInvalidHost(self):
        connect_args = dict({'host':''})
        connection = connect_to_region('us-west-2', **connect_args)
        self.assertEquals('s3-us-west-2.amazonaws.com', connection.host)
        self.assertIsInstance(connection, S3Connection)

    def testDefaultWithInvalidHostNone(self):
        connect_args = dict({'host':None})
        connection = connect_to_region('us-east-1', **connect_args)
        self.assertEquals('s3.amazonaws.com', connection.host)
        self.assertIsInstance(connection, S3Connection)

    def tearDown(self):
        self = connection = connect_args = None
