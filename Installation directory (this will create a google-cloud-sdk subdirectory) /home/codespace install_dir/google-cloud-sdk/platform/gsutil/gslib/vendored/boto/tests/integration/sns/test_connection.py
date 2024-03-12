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
from tests.compat import mock, unittest
from boto.compat import http_client
from boto.sns import connect_to_region


class StubResponse(object):
    status = 403
    reason = 'nopenopenope'

    def getheader(self, val):
        return b''

    def getheaders(self):
        return b''

    def read(self):
        return b''


class TestSNSConnection(unittest.TestCase):

    sns = True

    def setUp(self):
        self.connection = connect_to_region('us-west-2')

    def test_list_platform_applications(self):
        response = self.connection.list_platform_applications()

    def test_forced_host(self):
        # This test asserts that the ``Host`` header is correctly set.
        # On Python 2.5(.6), not having this in place would cause any SigV4
        # calls to fail, due to a signature mismatch (the port would be present
        # when it shouldn't be).
        https = http_client.HTTPConnection
        mpo = mock.patch.object

        with mpo(https, 'request') as mock_request:
            with mpo(https, 'getresponse', return_value=StubResponse()):
                with self.assertRaises(self.connection.ResponseError):
                    self.connection.list_platform_applications()

        # Now, assert that the ``Host`` was there & correct.
        call = mock_request.call_args_list[0]
        headers = call[0][3]
        self.assertTrue('Host' in headers)
        self.assertEqual(headers['Host'], 'sns.us-west-2.amazonaws.com')
