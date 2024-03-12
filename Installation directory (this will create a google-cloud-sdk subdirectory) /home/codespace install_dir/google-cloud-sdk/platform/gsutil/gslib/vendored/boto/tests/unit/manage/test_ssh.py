#!/usr/bin/env python
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

try:
    import paramiko
    from boto.manage.cmdshell import SSHClient
except ImportError:
    paramiko = None
    SSHClient = None

from tests.compat import mock, unittest


class TestSSHTimeout(unittest.TestCase):
    @unittest.skipIf(not paramiko, 'Paramiko missing')
    def test_timeout(self):
        client_tmp = paramiko.SSHClient

        def client_mock():
            client = client_tmp()
            client.connect = mock.Mock(name='connect')
            return client

        paramiko.SSHClient = client_mock
        paramiko.RSAKey.from_private_key_file = mock.Mock()

        server = mock.Mock()
        test = SSHClient(server)

        self.assertEqual(test._ssh_client.connect.call_args[1]['timeout'], None)

        test2 = SSHClient(server, timeout=30)

        self.assertEqual(test2._ssh_client.connect.call_args[1]['timeout'], 30)
