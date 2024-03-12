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
from boto.codedeploy.exceptions import ApplicationDoesNotExistException
from tests.compat import unittest


class TestCodeDeploy(unittest.TestCase):
    def setUp(self):
        self.codedeploy = boto.connect_codedeploy()

    def test_applications(self):
        application_name = 'my-boto-application'
        self.codedeploy.create_application(application_name=application_name)
        self.addCleanup(self.codedeploy.delete_application, application_name)
        response = self.codedeploy.list_applications()
        self.assertIn(application_name, response['applications'])

    def test_exception(self):
        with self.assertRaises(ApplicationDoesNotExistException):
            self.codedeploy.get_application('some-non-existant-app')
