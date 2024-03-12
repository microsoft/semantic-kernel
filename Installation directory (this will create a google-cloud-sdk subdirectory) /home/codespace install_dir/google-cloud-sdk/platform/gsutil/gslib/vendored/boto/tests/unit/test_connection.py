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
import os
import socket

from tests.compat import mock, unittest
from httpretty import HTTPretty

from boto import UserAgent
from boto.compat import json, parse_qs
from boto.connection import AWSQueryConnection, AWSAuthConnection, HTTPRequest
from boto.exception import BotoServerError
from boto.regioninfo import RegionInfo


class TestListParamsSerialization(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.connection = AWSQueryConnection('access_key', 'secret_key')

    def test_complex_list_serialization(self):
        # This example is taken from the doc string of
        # build_complex_list_params.
        params = {}
        self.connection.build_complex_list_params(
            params, [('foo', 'bar', 'baz'), ('foo2', 'bar2', 'baz2')],
            'ParamName.member', ('One', 'Two', 'Three'))
        self.assertDictEqual({
            'ParamName.member.1.One': 'foo',
            'ParamName.member.1.Two': 'bar',
            'ParamName.member.1.Three': 'baz',
            'ParamName.member.2.One': 'foo2',
            'ParamName.member.2.Two': 'bar2',
            'ParamName.member.2.Three': 'baz2',
        }, params)

    def test_simple_list_serialization(self):
        params = {}
        self.connection.build_list_params(
            params, ['foo', 'bar', 'baz'], 'ParamName.member')
        self.assertDictEqual({
            'ParamName.member.1': 'foo',
            'ParamName.member.2': 'bar',
            'ParamName.member.3': 'baz',
        }, params)


class MockAWSService(AWSQueryConnection):
    """
    Fake AWS Service

    This is used to test the AWSQueryConnection object is behaving properly.
    """

    APIVersion = '2012-01-01'

    def _required_auth_capability(self):
        return ['sign-v2']

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, host=None, port=None,
                 proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 api_version=None, security_token=None,
                 validate_certs=True, profile_name=None):
        self.region = region
        if host is None:
            host = self.region.endpoint
        AWSQueryConnection.__init__(self, aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    host, debug,
                                    https_connection_factory, path,
                                    security_token,
                                    validate_certs=validate_certs,
                                    profile_name=profile_name)


class TestAWSAuthConnection(unittest.TestCase):
    def test_get_path(self):
        conn = AWSAuthConnection(
            'mockservice.cc-zone-1.amazonaws.com',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret',
            suppress_consec_slashes=False
        )
        # Test some sample paths for mangling.
        self.assertEqual(conn.get_path('/'), '/')
        self.assertEqual(conn.get_path('image.jpg'), '/image.jpg')
        self.assertEqual(conn.get_path('folder/image.jpg'), '/folder/image.jpg')
        self.assertEqual(conn.get_path('folder//image.jpg'), '/folder//image.jpg')

        # Ensure leading slashes aren't removed.
        # See https://github.com/boto/boto/issues/1387
        self.assertEqual(conn.get_path('/folder//image.jpg'), '/folder//image.jpg')
        self.assertEqual(conn.get_path('/folder////image.jpg'), '/folder////image.jpg')
        self.assertEqual(conn.get_path('///folder////image.jpg'), '///folder////image.jpg')

    def test_connection_behind_proxy(self):
        os.environ['http_proxy'] = "http://john.doe:p4ssw0rd@127.0.0.1:8180"
        conn = AWSAuthConnection(
            'mockservice.cc-zone-1.amazonaws.com',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret',
            suppress_consec_slashes=False
        )
        self.assertEqual(conn.proxy, '127.0.0.1')
        self.assertEqual(conn.proxy_user, 'john.doe')
        self.assertEqual(conn.proxy_pass, 'p4ssw0rd')
        self.assertEqual(conn.proxy_port, '8180')
        del os.environ['http_proxy']

    def test_get_proxy_url_with_auth(self):
        conn = AWSAuthConnection(
            'mockservice.cc-zone-1.amazonaws.com',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret',
            suppress_consec_slashes=False,
            proxy="127.0.0.1",
            proxy_user="john.doe",
            proxy_pass="p4ssw0rd",
            proxy_port="8180"
        )
        self.assertEqual(conn.get_proxy_url_with_auth(), 'http://john.doe:p4ssw0rd@127.0.0.1:8180')

    def test_build_base_http_request_noproxy(self):
        os.environ['no_proxy'] = 'mockservice.cc-zone-1.amazonaws.com'

        conn = AWSAuthConnection(
            'mockservice.cc-zone-1.amazonaws.com',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret',
            suppress_consec_slashes=False,
            proxy="127.0.0.1",
            proxy_user="john.doe",
            proxy_pass="p4ssw0rd",
            proxy_port="8180"
        )
        request = conn.build_base_http_request('GET', '/', None)

        del os.environ['no_proxy']
        self.assertEqual(request.path, '/')

    def test_connection_behind_proxy_without_explicit_port(self):
        os.environ['http_proxy'] = "http://127.0.0.1"
        conn = AWSAuthConnection(
            'mockservice.cc-zone-1.amazonaws.com',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret',
            suppress_consec_slashes=False,
            port=8180
        )
        self.assertEqual(conn.proxy, '127.0.0.1')
        self.assertEqual(conn.proxy_port, 8180)
        del os.environ['http_proxy']

    @mock.patch.object(socket, 'create_connection')
    @mock.patch('boto.compat.http_client.HTTPResponse')
    @mock.patch('boto.connection.ssl', autospec=True)
    def test_proxy_ssl_with_verification(self, ssl_mock,
        http_response_mock,
        create_connection_mock):
      type(http_response_mock.return_value).status = mock.PropertyMock(
          return_value=200)

      conn = AWSAuthConnection(
          'mockservice.s3.amazonaws.com',
          aws_access_key_id='access_key',
          aws_secret_access_key='secret',
          suppress_consec_slashes=False,
          proxy_port=80
      )
      conn.https_validate_certificates = True
      dummy_cert = {
          'subjectAltName': (('DNS', 's3.amazonaws.com'),
                             ('DNS', '*.s3.amazonaws.com')),
      }
      mock_sock = mock.Mock()
      create_connection_mock.return_value = mock_sock
      mock_sslSock = mock.Mock()
      mock_sslSock.getpeercert.return_value = dummy_cert
      mock_context = mock.Mock()
      mock_context.wrap_socket.return_value = mock_sslSock
      ssl_mock.create_default_context.return_value = mock_context

      # Attempt to call proxy_ssl and make sure it works
      conn.proxy_ssl('mockservice.s3.amazonaws.com', 80)
      mock_sslSock.getpeercert.assert_called_once_with()
      mock_context.wrap_socket.assert_called_once_with(
          mock_sock,
          server_hostname='mockservice.s3.amazonaws.com')

    # this tests the proper setting of the host_header in v4 signing
    def test_host_header_with_nonstandard_port(self):
        # test standard port first
        conn = V4AuthConnection(
            'testhost',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret')
        request = conn.build_base_http_request(
            method='POST', path='/', auth_path=None, params=None, headers=None,
            data='', host=None)
        conn.set_host_header(request)
        self.assertEqual(request.headers['Host'], 'testhost')

        # next, test non-standard port
        conn = V4AuthConnection(
            'testhost',
            aws_access_key_id='access_key',
            aws_secret_access_key='secret',
            port=8773)
        request = conn.build_base_http_request(
            method='POST', path='/', auth_path=None, params=None, headers=None,
            data='', host=None)
        conn.set_host_header(request)
        self.assertEqual(request.headers['Host'], 'testhost:8773')


class V4AuthConnection(AWSAuthConnection):
    def __init__(self, host, aws_access_key_id, aws_secret_access_key, port=443):
        AWSAuthConnection.__init__(
            self, host, aws_access_key_id, aws_secret_access_key, port=port)

    def _required_auth_capability(self):
        return ['hmac-v4']


class TestAWSQueryConnection(unittest.TestCase):
    def setUp(self):
        self.region = RegionInfo(
            name='cc-zone-1',
            endpoint='mockservice.cc-zone-1.amazonaws.com',
            connection_cls=MockAWSService)

        HTTPretty.enable()

    def tearDown(self):
        HTTPretty.disable()


class TestAWSQueryConnectionSimple(TestAWSQueryConnection):
    def test_query_connection_basis(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/' % self.region.endpoint,
                               json.dumps({'test': 'secure'}),
                               content_type='application/json')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')

        self.assertEqual(conn.host, 'mockservice.cc-zone-1.amazonaws.com')

    def test_query_connection_noproxy(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/' % self.region.endpoint,
                               json.dumps({'test': 'secure'}),
                               content_type='application/json')

        os.environ['no_proxy'] = self.region.endpoint

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret',
                                   proxy="NON_EXISTENT_HOSTNAME",
                                   proxy_port="3128")

        resp = conn.make_request('myCmd',
                                 {'par1': 'foo', 'par2': 'baz'},
                                 "/",
                                 "POST")
        del os.environ['no_proxy']
        args = parse_qs(HTTPretty.last_request.body)
        self.assertEqual(args[b'AWSAccessKeyId'], [b'access_key'])

    def test_query_connection_noproxy_nosecure(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/' % self.region.endpoint,
                               json.dumps({'test': 'insecure'}),
                               content_type='application/json')

        os.environ['no_proxy'] = self.region.endpoint

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret',
                                   proxy="NON_EXISTENT_HOSTNAME",
                                   proxy_port="3128",
                                   is_secure=False)

        resp = conn.make_request('myCmd',
                                 {'par1': 'foo', 'par2': 'baz'},
                                 "/",
                                 "POST")
        del os.environ['no_proxy']
        args = parse_qs(HTTPretty.last_request.body)
        self.assertEqual(args[b'AWSAccessKeyId'], [b'access_key'])

    def test_single_command(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/' % self.region.endpoint,
                               json.dumps({'test': 'secure'}),
                               content_type='application/json')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')
        resp = conn.make_request('myCmd',
                                 {'par1': 'foo', 'par2': 'baz'},
                                 "/",
                                 "POST")

        args = parse_qs(HTTPretty.last_request.body)
        self.assertEqual(args[b'AWSAccessKeyId'], [b'access_key'])
        self.assertEqual(args[b'SignatureMethod'], [b'HmacSHA256'])
        self.assertEqual(args[b'Version'], [conn.APIVersion.encode('utf-8')])
        self.assertEqual(args[b'par1'], [b'foo'])
        self.assertEqual(args[b'par2'], [b'baz'])

        self.assertEqual(resp.read(), b'{"test": "secure"}')

    def test_multi_commands(self):
        """Check connection re-use"""
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/' % self.region.endpoint,
                               json.dumps({'test': 'secure'}),
                               content_type='application/json')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')

        resp1 = conn.make_request('myCmd1',
                                  {'par1': 'foo', 'par2': 'baz'},
                                  "/",
                                  "POST")
        body1 = parse_qs(HTTPretty.last_request.body)

        resp2 = conn.make_request('myCmd2',
                                  {'par3': 'bar', 'par4': 'narf'},
                                  "/",
                                  "POST")
        body2 = parse_qs(HTTPretty.last_request.body)

        self.assertEqual(body1[b'par1'], [b'foo'])
        self.assertEqual(body1[b'par2'], [b'baz'])
        with self.assertRaises(KeyError):
            body1[b'par3']

        self.assertEqual(body2[b'par3'], [b'bar'])
        self.assertEqual(body2[b'par4'], [b'narf'])
        with self.assertRaises(KeyError):
            body2['par1']

        self.assertEqual(resp1.read(), b'{"test": "secure"}')
        self.assertEqual(resp2.read(), b'{"test": "secure"}')

    def test_non_secure(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'http://%s/' % self.region.endpoint,
                               json.dumps({'test': 'normal'}),
                               content_type='application/json')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret',
                                   is_secure=False)
        resp = conn.make_request('myCmd1',
                                 {'par1': 'foo', 'par2': 'baz'},
                                 "/",
                                 "POST")

        self.assertEqual(resp.read(), b'{"test": "normal"}')

    def test_alternate_port(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'http://%s:8080/' % self.region.endpoint,
                               json.dumps({'test': 'alternate'}),
                               content_type='application/json')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret',
                                   port=8080,
                                   is_secure=False)
        resp = conn.make_request('myCmd1',
                                 {'par1': 'foo', 'par2': 'baz'},
                                 "/",
                                 "POST")

        self.assertEqual(resp.read(), b'{"test": "alternate"}')

    def test_temp_failure(self):
        responses = [HTTPretty.Response(body="{'test': 'fail'}", status=500),
                     HTTPretty.Response(body="{'test': 'success'}", status=200)]

        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/temp_fail/' % self.region.endpoint,
                               responses=responses)

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')
        resp = conn.make_request('myCmd1',
                                 {'par1': 'foo', 'par2': 'baz'},
                                 '/temp_fail/',
                                 'POST')
        self.assertEqual(resp.read(), b"{'test': 'success'}")

    def test_unhandled_exception(self):
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/temp_exception/' % self.region.endpoint,
                               responses=[])

        def fake_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
            raise socket.timeout('fake error')

        socket.create_connection = fake_connection

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')
        conn.num_retries = 0
        with self.assertRaises(socket.error):
            resp = conn.make_request('myCmd1',
                                     {'par1': 'foo', 'par2': 'baz'},
                                     '/temp_exception/',
                                     'POST')

    def test_connection_close(self):
        """Check connection re-use after close header is received"""
        HTTPretty.register_uri(HTTPretty.POST,
                               'https://%s/' % self.region.endpoint,
                               json.dumps({'test': 'secure'}),
                               content_type='application/json',
                               connection='close')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')

        def mock_put_conn(*args, **kwargs):
            raise Exception('put_http_connection should not be called!')

        conn.put_http_connection = mock_put_conn

        resp1 = conn.make_request('myCmd1',
                                  {'par1': 'foo', 'par2': 'baz'},
                                  "/",
                                  "POST")

        # If we've gotten this far then no exception was raised
        # by attempting to put the connection back into the pool
        # Now let's just confirm the close header was actually
        # set or we have another problem.
        self.assertEqual(resp1.getheader('connection'), 'close')

    def test_port_pooling(self):
        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret',
                                   port=8080)

        # Pick a connection, then put it back
        con1 = conn.get_http_connection(conn.host, conn.port, conn.is_secure)
        conn.put_http_connection(conn.host, conn.port, conn.is_secure, con1)

        # Pick another connection, which hopefully is the same yet again
        con2 = conn.get_http_connection(conn.host, conn.port, conn.is_secure)
        conn.put_http_connection(conn.host, conn.port, conn.is_secure, con2)

        self.assertEqual(con1, con2)

        # Change the port and make sure a new connection is made
        conn.port = 8081

        con3 = conn.get_http_connection(conn.host, conn.port, conn.is_secure)
        conn.put_http_connection(conn.host, conn.port, conn.is_secure, con3)

        self.assertNotEqual(con1, con3)


class TestAWSQueryStatus(TestAWSQueryConnection):

    def test_get_status(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               'https://%s/status' % self.region.endpoint,
                               '<status>ok</status>',
                               content_type='text/xml')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')
        resp = conn.get_status('getStatus',
                               {'par1': 'foo', 'par2': 'baz'},
                               'status')

        self.assertEqual(resp, "ok")

    def test_get_status_blank_error(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               'https://%s/status' % self.region.endpoint,
                               '',
                               content_type='text/xml')

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')
        with self.assertRaises(BotoServerError):
            resp = conn.get_status('getStatus',
                                   {'par1': 'foo', 'par2': 'baz'},
                                   'status')

    def test_get_status_error(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               'https://%s/status' % self.region.endpoint,
                               '<status>error</status>',
                               content_type='text/xml',
                               status=400)

        conn = self.region.connect(aws_access_key_id='access_key',
                                   aws_secret_access_key='secret')
        with self.assertRaises(BotoServerError):
            resp = conn.get_status('getStatus',
                                   {'par1': 'foo', 'par2': 'baz'},
                                   'status')


class TestHTTPRequest(unittest.TestCase):
    def test_user_agent_not_url_encoded(self):
        headers = {'Some-Header': u'should be encoded \u2713',
                   'User-Agent': UserAgent}
        request = HTTPRequest('PUT', 'https', 'amazon.com', 443, None,
                              None, {}, headers, 'Body')
        mock_connection = mock.Mock()

        # Create a method that preserves the headers at the time of
        # authorization.
        def mock_add_auth(req, **kwargs):
            mock_connection.headers_at_auth = req.headers.copy()

        mock_connection._auth_handler.add_auth = mock_add_auth

        request.authorize(mock_connection)
        # Ensure the headers at authorization are as expected i.e.
        # the user agent header was not url encoded but the other header was.
        self.assertEqual(mock_connection.headers_at_auth,
                         {'Some-Header': 'should be encoded %E2%9C%93',
                          'User-Agent': UserAgent})

    def test_content_length_str(self):
        request = HTTPRequest('PUT', 'https', 'amazon.com', 443, None,
                              None, {}, {}, 'Body')
        mock_connection = mock.Mock()
        request.authorize(mock_connection)

        # Ensure Content-Length header is a str. This is more explicit than
        # relying on other code cast the value later. (Python 2.7.0, for
        # example, assumes headers are of type str.)
        self.assertIsInstance(request.headers['Content-Length'], str)

if __name__ == '__main__':
    unittest.main()
