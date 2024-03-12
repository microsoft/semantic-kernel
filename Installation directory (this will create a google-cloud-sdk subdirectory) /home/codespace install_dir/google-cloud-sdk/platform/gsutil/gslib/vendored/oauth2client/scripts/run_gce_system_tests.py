# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import unittest

from six.moves import http_client
from six.moves import urllib

import oauth2client
from oauth2client import client
from oauth2client import transport
from oauth2client.contrib import gce


class TestComputeEngine(unittest.TestCase):

    def test_application_default(self):
        default_creds = client.GoogleCredentials.get_application_default()
        self.assertIsInstance(default_creds, gce.AppAssertionCredentials)

    def test_token_info(self):
        credentials = gce.AppAssertionCredentials([])
        http = transport.get_http_object()

        # First refresh to get the access token.
        self.assertIsNone(credentials.access_token)
        credentials.refresh(http)
        self.assertIsNotNone(credentials.access_token)

        # Then check the access token against the token info API.
        query_params = {'access_token': credentials.access_token}
        token_uri = (oauth2client.GOOGLE_TOKEN_INFO_URI + '?' +
                     urllib.parse.urlencode(query_params))
        response, content = transport.request(http, token_uri)
        self.assertEqual(response.status, http_client.OK)

        content = content.decode('utf-8')
        payload = json.loads(content)
        self.assertEqual(payload['access_type'], 'offline')
        self.assertLessEqual(int(payload['expires_in']), 3600)


if __name__ == '__main__':
    unittest.main()
