# Copyright 2017 Google Inc. All rights reserved.
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

"""Two factor Oauth2Credentials."""


import datetime
import json
import logging
import urllib

from oauth2client import _helpers
from oauth2client import client
from oauth2client import transport
from oauth2client.contrib import reauth
from oauth2client.contrib import reauth_errors

from six.moves import http_client


REAUTH_NEEDED_ERROR = 'invalid_grant'
REAUTH_NEEDED_ERROR_INVALID_RAPT = 'invalid_rapt'
REAUTH_NEEDED_ERROR_RAPT_REQUIRED = 'rapt_required'

logger = logging.getLogger(__name__)


class Oauth2WithReauthCredentials(client.OAuth2Credentials):
    """Credentials object that extends OAuth2Credentials with reauth support.

    This class provides the same functionality as OAuth2Credentials, but adds
    the support for reauthentication and rapt tokens. These credentials should
    behave the same as OAuth2Credentials when the credentials don't use rauth.
    """

    def __init__(self, *args, **kwargs):
        """Create an instance of Oauth2WithReauthCredentials.

        A Oauth2WithReauthCredentials has an extra rapt_token."""

        if 'rapt_token' in kwargs:
          self.rapt_token = kwargs['rapt_token']
          del kwargs['rapt_token']
        super(Oauth2WithReauthCredentials, self).__init__(*args, **kwargs)

    @classmethod
    def from_json(cls, json_data):
        """Overrides."""

        data = json.loads(_helpers._from_bytes(json_data))
        if (data.get('token_expiry') and
              not isinstance(data['token_expiry'], datetime.datetime)):
          try:
            data['token_expiry'] = datetime.datetime.strptime(
              data['token_expiry'], client.EXPIRY_FORMAT)
          except ValueError:
            data['token_expiry'] = None

        kwargs = {}
        for param in ('revoke_uri', 'id_token', 'id_token_jwt',
                      'token_response', 'scopes', 'token_info_uri',
                      'rapt_token'):
          value = data.get(param, None)
          if value is not None:
            kwargs[param] = value

        retval = cls(
          data['access_token'],
          data['client_id'],
          data['client_secret'],
          data['refresh_token'],
          data['token_expiry'],
          data['token_uri'],
          data['user_agent'],
          **kwargs
        )
        retval.invalid = data['invalid']
        return retval

    @classmethod
    def from_OAuth2Credentials(cls, original):
        """Instantiate a Oauth2WithReauthCredentials from OAuth2Credentials."""
        json = original.to_json()
        return cls.from_json(json)

    def _generate_refresh_request_body(self):
        """Overrides."""
        parameters = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'rapt': self.rapt_token,
        }
        body = urllib.parse.urlencode(parameters)
        return body

    def _handle_refresh_error(self, http, rapt_refreshed, resp, content):
        # Check if we need a rapt token or if the rapt token is invalid.
        # Once we refresh the rapt token, retry the access token refresh.
        # If we did refresh the rapt token and still got an error, then the
        # refresh token is expired or revoked.
        d = {}
        try:
            d = json.loads(content)
        except (TypeError, ValueError):
            pass

        if (not rapt_refreshed and d.get('error') == REAUTH_NEEDED_ERROR and
            (d.get('error_subtype') == REAUTH_NEEDED_ERROR_INVALID_RAPT or
             d.get('error_subtype') == REAUTH_NEEDED_ERROR_RAPT_REQUIRED)):
            self.rapt_token = reauth.GetRaptToken(
                getattr(http, 'request', http),
                self.client_id,
                self.client_secret,
                self.refresh_token,
                self.token_uri,
                scopes=list(self.scopes),
            )
            self._do_refresh_request(http, rapt_refreshed=True)
            return

        # An {'error':...} response body at this time means the refresh token
        # is expired or revoked, so we flag the credentials as such.
        logger.info('Failed to retrieve access token: {0}'.format(content))
        error_msg = 'Invalid response {0}.'.format(resp.status)
        if 'error' in d:
            error_msg = d['error']
            if 'error_description' in d:
                error_msg += ': ' + d['error_description']
            self.invalid = True
            if self.store is not None:
                self.store.locked_put(self)
        raise reauth_errors.HttpAccessTokenRefreshError(
          error_msg, status=resp.status)

    def _do_refresh_request(self, http, rapt_refreshed=False):
      """Refresh the access_token using the refresh_token.

      Args:
          http: An object to be used to make HTTP requests.
          rapt_refreshed: If we did or did not already refreshed the rapt
                          token.

      Raises:
          HttpAccessTokenRefreshError: When the refresh fails.
      """
      body = self._generate_refresh_request_body()
      headers = self._generate_refresh_request_headers()

      logger.info('Refreshing access_token')
      resp, content = transport.request(
          http, self.token_uri, method='POST',
          body=body, headers=headers)
      content = _helpers._from_bytes(content)

      if resp.status != http_client.OK:
          self._handle_refresh_error(http, rapt_refreshed, resp, content)
          return

      d = json.loads(content)
      self.token_response = d
      self.access_token = d['access_token']
      self.refresh_token = d.get('refresh_token', self.refresh_token)
      if 'expires_in' in d:
          delta = datetime.timedelta(seconds=int(d['expires_in']))
          self.token_expiry = delta + client._UTCNOW()
      else:
          self.token_expiry = None
      if 'id_token' in d:
          self.id_token = client._extract_id_token(d['id_token'])
          self.id_token_jwt = d['id_token']
      else:
          self.id_token = None
          self.id_token_jwt = None
      # On temporary refresh errors, the user does not actually have to
      # re-authorize, so we unflag here.
      self.invalid = False
      if self.store:
          self.store.locked_put(self)
