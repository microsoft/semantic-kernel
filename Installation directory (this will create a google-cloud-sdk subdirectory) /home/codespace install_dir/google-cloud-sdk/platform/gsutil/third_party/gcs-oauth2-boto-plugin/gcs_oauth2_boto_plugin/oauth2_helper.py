# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Helper routines to facilitate use of oauth2_client."""

from __future__ import absolute_import

import io
import json
import os
import sys
import time
import webbrowser

from gcs_oauth2_boto_plugin import oauth2_client
import oauth2client.client

from six.moves import input  # pylint: disable=redefined-builtin

UTF8 = 'utf-8'
CLIENT_ID = None
CLIENT_SECRET = None

GOOGLE_OAUTH2_PROVIDER_AUTHORIZATION_URI = (
    'https://accounts.google.com/o/oauth2/auth')
GOOGLE_OAUTH2_PROVIDER_TOKEN_URI = (
    'https://oauth2.googleapis.com/token')
GOOGLE_OAUTH2_DEFAULT_FILE_PASSWORD = 'notasecret'

OOB_REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'


def OAuth2ClientFromBotoConfig(
    config, cred_type=oauth2_client.CredTypes.OAUTH2_USER_ACCOUNT):
  """Create a client type based on credentials supplied in boto config."""
  token_cache = None
  token_cache_type = config.get('OAuth2', 'token_cache', 'file_system')
  if token_cache_type == 'file_system':
    if config.has_option('OAuth2', 'token_cache_path_pattern'):
      token_cache = oauth2_client.FileSystemTokenCache(
          path_pattern=config.get('OAuth2', 'token_cache_path_pattern'))
    else:
      token_cache = oauth2_client.FileSystemTokenCache()
  elif token_cache_type == 'in_memory':
    token_cache = oauth2_client.InMemoryTokenCache()
  else:
    raise Exception(
        'Invalid value for config option OAuth2/token_cache: %s' %
        token_cache_type)

  proxy_host = None
  proxy_port = None
  proxy_user = None
  proxy_pass = None
  if (config.has_option('Boto', 'proxy')
      and config.has_option('Boto', 'proxy_port')):
    proxy_host = config.get('Boto', 'proxy')
    proxy_port = int(config.get('Boto', 'proxy_port'))
    proxy_user = config.get('Boto', 'proxy_user', None)
    proxy_pass = config.get('Boto', 'proxy_pass', None)

  provider_authorization_uri = config.get(
      'OAuth2', 'provider_authorization_uri',
      GOOGLE_OAUTH2_PROVIDER_AUTHORIZATION_URI)
  provider_token_uri = config.get(
      'OAuth2', 'provider_token_uri', GOOGLE_OAUTH2_PROVIDER_TOKEN_URI)

  if cred_type == oauth2_client.CredTypes.OAUTH2_SERVICE_ACCOUNT:
    service_client_id = config.get('Credentials', 'gs_service_client_id', '')
    private_key_filename = config.get('Credentials', 'gs_service_key_file', '')
    with io.open(private_key_filename, 'rb') as private_key_file:
      private_key = private_key_file.read()

    keyfile_is_utf8 = False
    try:
      private_key = private_key.decode(UTF8)
      # P12 keys won't be encoded as UTF8 bytes.
      keyfile_is_utf8 = True
    except UnicodeDecodeError:
      pass

    if keyfile_is_utf8:
      try:
        json_key_dict = json.loads(private_key)
      except ValueError:
        raise Exception('Could not parse JSON keyfile "%s" as valid JSON' %
                        private_key_filename)
      for json_entry in ('client_id', 'client_email', 'private_key_id',
                         'private_key'):
        if json_entry not in json_key_dict:
          raise Exception('The JSON private key file at %s '
                          'did not contain the required entry: %s' %
                          (private_key_filename, json_entry))
      return oauth2_client.OAuth2JsonServiceAccountClient(
          json_key_dict, access_token_cache=token_cache,
          auth_uri=provider_authorization_uri, token_uri=provider_token_uri,
          disable_ssl_certificate_validation=not(config.getbool(
              'Boto', 'https_validate_certificates', True)),
          proxy_host=proxy_host, proxy_port=proxy_port,
          proxy_user=proxy_user, proxy_pass=proxy_pass)
    else:
      key_file_pass = config.get('Credentials', 'gs_service_key_file_password',
                                 GOOGLE_OAUTH2_DEFAULT_FILE_PASSWORD)

      return oauth2_client.OAuth2ServiceAccountClient(
          service_client_id, private_key, key_file_pass,
          access_token_cache=token_cache, auth_uri=provider_authorization_uri,
          token_uri=provider_token_uri,
          disable_ssl_certificate_validation=not(config.getbool(
              'Boto', 'https_validate_certificates', True)),
          proxy_host=proxy_host, proxy_port=proxy_port,
          proxy_user=proxy_user, proxy_pass=proxy_pass)

  elif cred_type == oauth2_client.CredTypes.OAUTH2_USER_ACCOUNT:
    client_id = config.get('OAuth2', 'client_id',
                           os.environ.get('OAUTH2_CLIENT_ID', CLIENT_ID))
    if not client_id:
      raise Exception(
          'client_id for your application obtained from '
          'https://console.developers.google.com must be set in a boto config '
          'or with OAUTH2_CLIENT_ID environment variable or with '
          'gcs_oauth2_boto_plugin.SetFallbackClientIdAndSecret function.')

    client_secret = config.get('OAuth2', 'client_secret',
                               os.environ.get('OAUTH2_CLIENT_SECRET',
                                              CLIENT_SECRET))
    ca_certs_file = config.get_value('Boto', 'ca_certificates_file')
    if ca_certs_file == 'system':
      ca_certs_file = None

    if not client_secret:
      raise Exception(
          'client_secret for your application obtained from '
          'https://console.developers.google.com must be set in a boto config '
          'or with OAUTH2_CLIENT_SECRET environment variable or with '
          'gcs_oauth2_boto_plugin.SetFallbackClientIdAndSecret function.')
    return oauth2_client.OAuth2UserAccountClient(
        provider_token_uri, client_id, client_secret,
        config.get('Credentials', 'gs_oauth2_refresh_token'),
        auth_uri=provider_authorization_uri, access_token_cache=token_cache,
        disable_ssl_certificate_validation=not(config.getbool(
            'Boto', 'https_validate_certificates', True)),
        proxy_host=proxy_host, proxy_port=proxy_port,
        proxy_user=proxy_user, proxy_pass=proxy_pass,
        ca_certs_file=ca_certs_file)
  else:
    raise Exception('You have attempted to create an OAuth2 client without '
                    'setting up OAuth2 credentials.')


def OAuth2ApprovalFlow(client, scopes, launch_browser=False):
  """Run the OAuth2 flow to fetch a refresh token. Returns the refresh token."""
  flow = oauth2client.client.OAuth2WebServerFlow(
      client.client_id, client.client_secret, scopes, auth_uri=client.auth_uri,
      token_uri=client.token_uri, redirect_uri=OOB_REDIRECT_URI)
  approval_url = flow.step1_get_authorize_url()

  if launch_browser:
    sys.stdout.write(
        'Attempting to launch a browser with the OAuth2 approval dialog at '
        'URL: %s\n\n'
        '[Note: due to a Python bug, you may see a spurious error message '
        '"object is not\ncallable [...] in [...] Popen.__del__" which can be '
        'ignored.]\n\n' % approval_url)
  else:
    sys.stdout.write(
        'Please navigate your browser to the following URL:\n%s\n' %
        approval_url)

  sys.stdout.write(
      'In your browser you should see a page that requests you to authorize '
      'access to Google Cloud Platform APIs and Services on your behalf. '
      'After you approve, an authorization code will be displayed.\n\n')
  if (launch_browser and
      not webbrowser.open(approval_url, new=1, autoraise=True)):
    sys.stdout.write(
        'Launching browser appears to have failed; please navigate a browser '
        'to the following URL:\n%s\n' % approval_url)
  # Short delay; webbrowser.open on linux insists on printing out a message
  # which we don't want to run into the prompt for the auth code.
  time.sleep(2)
  code = input('Enter the authorization code: ')
  credentials = flow.step2_exchange(code, http=client.CreateHttpRequest())
  return credentials.refresh_token


def SetFallbackClientIdAndSecret(client_id, client_secret):
  global CLIENT_ID
  global CLIENT_SECRET

  CLIENT_ID = client_id
  CLIENT_SECRET = client_secret


def SetLock(lock):
  oauth2_client.token_exchange_lock = lock

