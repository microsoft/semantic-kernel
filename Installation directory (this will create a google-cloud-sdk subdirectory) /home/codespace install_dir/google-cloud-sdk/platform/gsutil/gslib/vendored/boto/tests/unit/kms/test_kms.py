# Copyright (c) 2013 Amazon.com, Inc. or its affiliates. All Rights Reserved
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

from boto.compat import json
from boto.kms.layer1 import KMSConnection
from tests.unit import AWSMockServiceTestCase


class TestKinesis(AWSMockServiceTestCase):
    connection_class = KMSConnection

    def default_body(self):
        return b'{}'

    def test_binary_input(self):
        """
        This test ensures that binary is base64 encoded when it is sent to
        the service.
        """
        self.set_http_response(status_code=200)
        data = b'\x00\x01\x02\x03\x04\x05'
        self.service_connection.encrypt(key_id='foo', plaintext=data)
        body = json.loads(self.actual_request.body.decode('utf-8'))
        self.assertEqual(body['Plaintext'], 'AAECAwQF')

    def test_non_binary_input_for_blobs_fails(self):
        """
        This test ensures that only binary is used for blob type parameters.
        """ 
        self.set_http_response(status_code=200)
        data = u'\u00e9'
        with self.assertRaises(TypeError):
            self.service_connection.encrypt(key_id='foo', plaintext=data)

    def test_binary_ouput(self):
        """
        This test ensures that the output is base64 decoded before
        it is returned to the user.
        """
        content = {'Plaintext': 'AAECAwQF'}
        self.set_http_response(status_code=200,
                               body=json.dumps(content).encode('utf-8'))
        response = self.service_connection.decrypt(b'some arbitrary value')
        self.assertEqual(response['Plaintext'], b'\x00\x01\x02\x03\x04\x05')
