# Copyright (c) 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved
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
import tempfile
import shutil
import os
import socket

from boto.compat import json
from boto.awslambda.layer1 import AWSLambdaConnection
from tests.unit import AWSMockServiceTestCase
from tests.compat import mock


class TestAWSLambda(AWSMockServiceTestCase):
    connection_class = AWSLambdaConnection
    
    def default_body(self):
        return b'{}'

    def test_upload_function_binary(self):
        self.set_http_response(status_code=201)
        function_data = b'This is my file'
        self.service_connection.upload_function(
            function_name='my-function',
            function_zip=function_data,
            role='myrole',
            handler='myhandler',
            mode='event',
            runtime='nodejs'
        )
        self.assertEqual(self.actual_request.body, function_data)
        self.assertEqual(
            self.actual_request.headers['Content-Length'],
            str(len(function_data))
        )
        self.assertEqual(
            self.actual_request.path,
            '/2014-11-13/functions/my-function?Handler=myhandler&Mode'
            '=event&Role=myrole&Runtime=nodejs'
        )

    def test_upload_function_file(self):
        self.set_http_response(status_code=201)
        rootdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, rootdir)

        filename = 'test_file'
        function_data = b'This is my file'
        full_path = os.path.join(rootdir, filename)

        with open(full_path, 'wb') as f:
            f.write(function_data)

        with open(full_path, 'rb') as f:
            self.service_connection.upload_function(
                function_name='my-function',
                function_zip=f,
                role='myrole',
                handler='myhandler',
                mode='event',
                runtime='nodejs'
            )
            self.assertEqual(self.actual_request.body.read(),
                             function_data)
            self.assertEqual(
                self.actual_request.headers['Content-Length'],
                str(len(function_data))
            )
            self.assertEqual(
                self.actual_request.path,
                '/2014-11-13/functions/my-function?Handler=myhandler&Mode'
                '=event&Role=myrole&Runtime=nodejs'
            )

    def test_upload_function_unseekable_file_no_tell(self):
        sock = socket.socket()
        with self.assertRaises(TypeError):
            self.service_connection.upload_function(
                function_name='my-function',
                function_zip=sock,
                role='myrole',
                handler='myhandler',
                mode='event',
                runtime='nodejs'
            )

    def test_upload_function_unseekable_file_cannot_tell(self):
        mock_file = mock.Mock()
        mock_file.tell.side_effect = IOError
        with self.assertRaises(TypeError):
            self.service_connection.upload_function(
                function_name='my-function',
                function_zip=mock_file,
                role='myrole',
                handler='myhandler',
                mode='event',
                runtime='nodejs'
            )
