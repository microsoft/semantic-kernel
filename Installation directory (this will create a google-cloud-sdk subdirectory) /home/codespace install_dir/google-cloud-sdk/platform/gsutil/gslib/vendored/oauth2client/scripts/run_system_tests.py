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
import os

from six.moves import http_client

import oauth2client
from oauth2client import client
from oauth2client import service_account
from oauth2client import transport


JSON_KEY_PATH = os.getenv('OAUTH2CLIENT_TEST_JSON_KEY_PATH')
P12_KEY_PATH = os.getenv('OAUTH2CLIENT_TEST_P12_KEY_PATH')
P12_KEY_EMAIL = os.getenv('OAUTH2CLIENT_TEST_P12_KEY_EMAIL')
USER_KEY_PATH = os.getenv('OAUTH2CLIENT_TEST_USER_KEY_PATH')
USER_KEY_EMAIL = os.getenv('OAUTH2CLIENT_TEST_USER_KEY_EMAIL')

SCOPE = ('https://www.googleapis.com/auth/plus.login',
         'https://www.googleapis.com/auth/plus.me',
         'https://www.googleapis.com/auth/userinfo.email',
         'https://www.googleapis.com/auth/userinfo.profile')
USER_INFO = 'https://www.googleapis.com/oauth2/v2/userinfo'


def _require_environ():
    if (JSON_KEY_PATH is None or P12_KEY_PATH is None or
            P12_KEY_EMAIL is None or USER_KEY_PATH is None or
            USER_KEY_EMAIL is None):
        raise EnvironmentError('Expected environment variables to be set:',
                               'OAUTH2CLIENT_TEST_JSON_KEY_PATH',
                               'OAUTH2CLIENT_TEST_P12_KEY_PATH',
                               'OAUTH2CLIENT_TEST_P12_KEY_EMAIL',
                               'OAUTH2CLIENT_TEST_USER_KEY_PATH',
                               'OAUTH2CLIENT_TEST_USER_KEY_EMAIL')

    if not os.path.isfile(JSON_KEY_PATH):
        raise EnvironmentError(JSON_KEY_PATH, 'is not a file')
    if not os.path.isfile(P12_KEY_PATH):
        raise EnvironmentError(P12_KEY_PATH, 'is not a file')
    if not os.path.isfile(USER_KEY_PATH):
        raise EnvironmentError(USER_KEY_PATH, 'is not a file')


def _check_user_info(credentials, expected_email):
    http = credentials.authorize(transport.get_http_object())
    response, content = transport.request(http, USER_INFO)
    if response.status != http_client.OK:
        raise ValueError('Expected 200 OK response.')

    content = content.decode('utf-8')
    payload = json.loads(content)
    if payload['email'] != expected_email:
        raise ValueError('User info email does not match credentials.')


def run_json():
    factory = service_account.ServiceAccountCredentials.from_json_keyfile_name
    credentials = factory(JSON_KEY_PATH, scopes=SCOPE)
    service_account_email = credentials._service_account_email
    _check_user_info(credentials, service_account_email)


def run_p12():
    credentials = service_account.ServiceAccountCredentials.from_p12_keyfile(
        P12_KEY_EMAIL, P12_KEY_PATH, scopes=SCOPE)
    _check_user_info(credentials, P12_KEY_EMAIL)


def run_user_json():
    with open(USER_KEY_PATH, 'r') as file_object:
        client_credentials = json.load(file_object)

    credentials = client.GoogleCredentials(
        access_token=None,
        client_id=client_credentials['client_id'],
        client_secret=client_credentials['client_secret'],
        refresh_token=client_credentials['refresh_token'],
        token_expiry=None,
        token_uri=oauth2client.GOOGLE_TOKEN_URI,
        user_agent='Python client library',
    )

    _check_user_info(credentials, USER_KEY_EMAIL)


def main():
    _require_environ()
    run_json()
    run_p12()
    run_user_json()


if __name__ == '__main__':
    main()
