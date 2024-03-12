# Copyright (c) 2016 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from tests.compat import mock, unittest

from boto.pyami import config
from boto.compat import StringIO


class TestCanLoadConfigFile(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.file_contents = StringIO()
        file_contents = StringIO(
            '[Boto]\n'
            'https_validate_certificates = true\n'
            'other = false\n'
            'http_socket_timeout = 1\n'
            '[Credentials]\n'
            'aws_access_key_id=foo\n'
            'aws_secret_access_key=bar\n'
        )
        self.config = config.Config(fp=file_contents)

    def test_can_get_bool(self):
        self.assertTrue(
            self.config.getbool('Boto', 'https_validate_certificates'))
        self.assertFalse(self.config.getbool('Boto', 'other'))
        self.assertFalse(self.config.getbool('Boto', 'does-not-exist'))

    def test_can_get_int(self):
        self.assertEqual(self.config.getint('Boto', 'http_socket_timeout'), 1)
        self.assertEqual(self.config.getint('Boto', 'does-not-exist'), 0)
        self.assertEqual(
            self.config.getint('Boto', 'does-not-exist', default=20), 20)

    def test_can_get_strings(self):
        self.assertEqual(
            self.config.get('Credentials', 'aws_access_key_id'), 'foo')
        self.assertIsNone(
            self.config.get('Credentials', 'no-exist'))
        self.assertEqual(
            self.config.get('Credentials', 'no-exist', 'default-value'),
            'default-value')
