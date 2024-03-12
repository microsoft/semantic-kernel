# Copyright 2011 Google Inc.
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
Tests to validate correct validation of SSL server certificates.

Note that this test assumes two external dependencies are available:
  - A http proxy, which by default is assumed to be at host 'cache' and port
    3128.  This can be overridden with environment variables PROXY_HOST and
    PROXY_PORT, respectively.
  - An ssl-enabled web server that will return a valid certificate signed by one
    of the bundled CAs, and which can be reached by an alternate hostname that
    does not match the CN in that certificate.  By default, this test uses host
    'www' (without fully qualified domain). This can be overridden with
    environment variable INVALID_HOSTNAME_HOST. If no suitable host is already
    available, such a mapping can be established by temporarily adding an IP
    address for, say, www.google.com or www.amazon.com to /etc/hosts.
"""

import os
import ssl
import unittest
import mock

from nose.plugins.attrib import attr

import boto
from boto.pyami.config import Config
from boto import exception, https_connection
from boto.gs.connection import GSConnection
from boto.s3.connection import S3Connection


# File 'other_cacerts.txt' contains a valid CA certificate of a CA that is used
# by neither S3 nor Google Cloud Storage. Validation against this CA cert should
# result in a certificate error.
DEFAULT_CA_CERTS_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__ )), 'other_cacerts.txt')


PROXY_HOST = os.environ.get('PROXY_HOST', 'cache')
PROXY_PORT = os.environ.get('PROXY_PORT', '3128')

# This test assumes that this host returns a certificate signed by one of the
# trusted CAs, but with a Common Name that won't match host name 'www' (i.e.,
# the server should return a certificate with CN 'www.<somedomain>.com').
INVALID_HOSTNAME_HOST = os.environ.get('INVALID_HOSTNAME_HOST', 'www')


@attr('notdefault', 'ssl')
class CertValidationTest(unittest.TestCase):
    def setUp(self):
        self.config = Config()

        # Enable https_validate_certificates.
        self.config.add_section('Boto')
        self.config.setbool('Boto', 'https_validate_certificates', True)

        # Set up bogus credentials so that the auth module is willing to go
        # ahead and make a request; the request should fail with a service-level
        # error if it does get to the service (S3 or GS).
        self.config.add_section('Credentials')
        self.config.set('Credentials', 'gs_access_key_id', 'xyz')
        self.config.set('Credentials', 'gs_secret_access_key', 'xyz')
        self.config.set('Credentials', 'aws_access_key_id', 'xyz')
        self.config.set('Credentials', 'aws_secret_access_key', 'xyz')

        self._config_patch = mock.patch('boto.config', self.config)
        self._config_patch.start()

    def tearDown(self):
        self._config_patch.stop()

    def enableProxy(self):
        self.config.set('Boto', 'proxy', PROXY_HOST)
        self.config.set('Boto', 'proxy_port', PROXY_PORT)

    def assertConnectionThrows(self, connection_class, error):
        conn = connection_class('fake_id', 'fake_secret')
        self.assertRaises(error, conn.get_all_buckets)

    def do_test_valid_cert(self):
        # When connecting to actual servers with bundled root certificates, no
        # cert errors should be thrown; instead we will get "invalid
        # credentials" errors since the config used does not contain any
        # credentials.
        self.assertConnectionThrows(S3Connection, exception.S3ResponseError)
        self.assertConnectionThrows(GSConnection, exception.GSResponseError)

    def test_valid_cert(self):
        self.do_test_valid_cert()

    def test_valid_cert_with_proxy(self):
        self.enableProxy()
        self.do_test_valid_cert()

    def do_test_invalid_signature(self):
        self.config.set('Boto', 'ca_certificates_file', DEFAULT_CA_CERTS_FILE)
        self.assertConnectionThrows(S3Connection, ssl.SSLError)
        self.assertConnectionThrows(GSConnection, ssl.SSLError)

    def test_invalid_signature(self):
        self.do_test_invalid_signature()

    def test_invalid_signature_with_proxy(self):
        self.enableProxy()
        self.do_test_invalid_signature()

    def do_test_invalid_host(self):
        self.config.set('Credentials', 'gs_host', INVALID_HOSTNAME_HOST)
        self.config.set('Credentials', 's3_host', INVALID_HOSTNAME_HOST)
        self.assertConnectionThrows(S3Connection, ssl.SSLError)
        self.assertConnectionThrows(GSConnection, ssl.SSLError)

    def do_test_invalid_host(self):
        self.config.set('Credentials', 'gs_host', INVALID_HOSTNAME_HOST)
        self.config.set('Credentials', 's3_host', INVALID_HOSTNAME_HOST)
        self.assertConnectionThrows(
                S3Connection, https_connection.InvalidCertificateException)
        self.assertConnectionThrows(
                GSConnection, https_connection.InvalidCertificateException)

    def test_invalid_host(self):
        self.do_test_invalid_host()

    def test_invalid_host_with_proxy(self):
        self.enableProxy()
        self.do_test_invalid_host()

