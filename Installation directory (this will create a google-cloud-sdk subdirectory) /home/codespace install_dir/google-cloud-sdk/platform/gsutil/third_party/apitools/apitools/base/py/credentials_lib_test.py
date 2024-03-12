#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os.path
import shutil
import tempfile
import unittest

import mock
import six

from apitools.base.py import credentials_lib
from apitools.base.py import util


class MetadataMock(object):

    def __init__(self, scopes=None, service_account_name=None):
        self._scopes = scopes or ['scope1']
        self._sa = service_account_name or 'default'

    def __call__(self, request_url):
        if request_url.endswith('scopes'):
            return six.StringIO(''.join(self._scopes))
        elif request_url.endswith('service-accounts'):
            return six.StringIO(self._sa)
        elif request_url.endswith(
                '/service-accounts/%s/token' % self._sa):
            return six.StringIO('{"access_token": "token"}')
        self.fail('Unexpected HTTP request to %s' % request_url)


class CredentialsLibTest(unittest.TestCase):

    def _RunGceAssertionCredentials(
            self, service_account_name=None, scopes=None, cache_filename=None):
        kwargs = {}
        if service_account_name is not None:
            kwargs['service_account_name'] = service_account_name
        if cache_filename is not None:
            kwargs['cache_filename'] = cache_filename
        service_account_name = service_account_name or 'default'
        credentials = credentials_lib.GceAssertionCredentials(
            scopes, **kwargs)
        self.assertIsNone(credentials._refresh(None))
        return credentials

    def _GetServiceCreds(self, service_account_name=None, scopes=None):
        metadatamock = MetadataMock(scopes, service_account_name)
        with mock.patch.object(util, 'DetectGce', autospec=True) as gce_detect:
            gce_detect.return_value = True
            with mock.patch.object(credentials_lib,
                                   '_GceMetadataRequest',
                                   side_effect=metadatamock,
                                   autospec=True) as opener_mock:
                credentials = self._RunGceAssertionCredentials(
                    service_account_name=service_account_name,
                    scopes=scopes)
            self.assertEqual(3, opener_mock.call_count)
        return credentials

    def testGceServiceAccounts(self):
        scopes = ['scope1']
        self._GetServiceCreds(service_account_name=None,
                              scopes=None)
        self._GetServiceCreds(service_account_name=None,
                              scopes=scopes)
        self._GetServiceCreds(
            service_account_name='my_service_account',
            scopes=scopes)

    def testGceAssertionCredentialsToJson(self):
        scopes = ['scope1']
        service_account_name = 'my_service_account'
        # Ensure that we can obtain a JSON representation of
        # GceAssertionCredentials to put in a credential Storage object, and
        # that the JSON representation is valid.
        original_creds = self._GetServiceCreds(
            service_account_name=service_account_name,
            scopes=scopes)
        original_creds_json_str = original_creds.to_json()
        json.loads(original_creds_json_str)

    @mock.patch.object(util, 'DetectGce', autospec=True)
    def testGceServiceAccountsCached(self, mock_detect):
        mock_detect.return_value = True
        tempd = tempfile.mkdtemp()
        tempname = os.path.join(tempd, 'creds')
        scopes = ['scope1']
        service_account_name = 'some_service_account_name'
        metadatamock = MetadataMock(scopes, service_account_name)
        with mock.patch.object(credentials_lib,
                               '_GceMetadataRequest',
                               side_effect=metadatamock,
                               autospec=True) as opener_mock:
            try:
                creds1 = self._RunGceAssertionCredentials(
                    service_account_name=service_account_name,
                    cache_filename=tempname,
                    scopes=scopes)
                pre_cache_call_count = opener_mock.call_count
                creds2 = self._RunGceAssertionCredentials(
                    service_account_name=service_account_name,
                    cache_filename=tempname,
                    scopes=None)
            finally:
                shutil.rmtree(tempd)
        self.assertEqual(creds1.client_id, creds2.client_id)
        self.assertEqual(pre_cache_call_count, 3)
        # Caching obviates the need for extra metadata server requests.
        # Only one metadata request is made if the cache is hit.
        self.assertEqual(opener_mock.call_count, 4)

    def testGetServiceAccount(self):
        # We'd also like to test the metadata calls, which requires
        # having some knowledge about how HTTP calls are made (so that
        # we can mock them). It's unfortunate, but there's no way
        # around it.
        creds = self._GetServiceCreds()
        opener = mock.MagicMock()
        opener.open = mock.MagicMock()
        opener.open.return_value = six.StringIO('default/\nanother')
        with mock.patch.object(six.moves.urllib.request, 'build_opener',
                               return_value=opener,
                               autospec=True) as build_opener:
            creds.GetServiceAccount('default')
            self.assertEqual(1, build_opener.call_count)
            self.assertEqual(1, opener.open.call_count)
            req = opener.open.call_args[0][0]
            self.assertTrue(req.get_full_url().startswith(
                'http://metadata.google.internal/'))
            # The urllib module does weird things with header case.
            self.assertEqual('Google', req.get_header('Metadata-flavor'))

    def testGetAdcNone(self):
        # Tests that we correctly return None when ADC aren't present in
        # the well-known file.
        creds = credentials_lib._GetApplicationDefaultCredentials(
            client_info={'scope': ''})
        self.assertIsNone(creds)


class TestGetRunFlowFlags(unittest.TestCase):

    def setUp(self):
        self._flags_actual = credentials_lib.FLAGS

    def tearDown(self):
        credentials_lib.FLAGS = self._flags_actual

    def test_with_gflags(self):
        HOST = 'myhostname'
        PORT = '144169'

        class MockFlags(object):
            auth_host_name = HOST
            auth_host_port = PORT
            auth_local_webserver = False

        credentials_lib.FLAGS = MockFlags
        flags = credentials_lib._GetRunFlowFlags([
            '--auth_host_name=%s' % HOST,
            '--auth_host_port=%s' % PORT,
            '--noauth_local_webserver',
        ])
        self.assertEqual(flags.auth_host_name, HOST)
        self.assertEqual(flags.auth_host_port, PORT)
        self.assertEqual(flags.logging_level, 'ERROR')
        self.assertEqual(flags.noauth_local_webserver, True)

    def test_without_gflags(self):
        credentials_lib.FLAGS = None
        flags = credentials_lib._GetRunFlowFlags([])
        self.assertEqual(flags.auth_host_name, 'localhost')
        self.assertEqual(flags.auth_host_port, [8080, 8090])
        self.assertEqual(flags.logging_level, 'ERROR')
        self.assertEqual(flags.noauth_local_webserver, False)
