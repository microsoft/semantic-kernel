#!/usr/bin/env python
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

from oauth2client_4_0 import _helpers
from oauth2client_4_0 import client
from oauth2client_4_0 import transport
from google_reauth import errors
from google_reauth import reauth


_LOGGER = logging.getLogger(__name__)


class Oauth2WithReauthCredentials(client.OAuth2Credentials):
    """Credentials object that extends OAuth2Credentials with reauth support.

    This class provides the same functionality as OAuth2Credentials, but adds
    the support for reauthentication and rapt tokens. These credentials should
    behave the same as OAuth2Credentials when the credentials don't use rauth.
    """

    def __init__(self, *args, **kwargs):
        """Create an instance of Oauth2WithReauthCredentials.

        A Oauth2WithReauthCredentials has an extra rapt_token."""

        self.rapt_token = kwargs.pop('rapt_token', None)
        super(Oauth2WithReauthCredentials, self).__init__(*args, **kwargs)

    @classmethod
    def from_json(cls, json_data):
        """Overrides."""

        data = json.loads(_helpers._from_bytes(json_data))
        if ((data.get('token_expiry')
             and not isinstance(data['token_expiry'], datetime.datetime))):
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

    def _do_refresh_request(self, http):
        """Refresh the access_token using the refresh_token.

        Args:
            http: An object to be used to make HTTP requests.
            rapt_refreshed: If we did or did not already refreshed the rapt
                            token.

        Raises:
            oauth2client_4_0.client.HttpAccessTokenRefreshError: if the refresh
                fails.
        """
        headers = self._generate_refresh_request_headers()

        _LOGGER.info('Refreshing access_token')

        def http_request(uri, method, body, headers):
            response, content = transport.request(
                http, uri, method=method,
                body=body, headers=headers)
            content = _helpers._from_bytes(content)
            return response, content

        try:
            self._update(*reauth.refresh_access_token(
                    http_request,
                    self.client_id,
                    self.client_secret,
                    self.refresh_token,
                    self.token_uri,
                    rapt=self.rapt_token,
                    scopes=list(self.scopes),
                    headers=headers))
        except (errors.ReauthAccessTokenRefreshError,
                errors.HttpAccessTokenRefreshError) as e:
            self.invalid = True
            if self.store:
                self.store.locked_put(self)
            raise client.HttpAccessTokenRefreshError(e, status=e.status)

    def _update(self, rapt, content, access_token, refresh_token=None,
                expires_in=None, id_token=None):
        if rapt:
            self.rapt_token = rapt
        self.token_response = content
        self.access_token = access_token
        self.refresh_token = (
            refresh_token if refresh_token else self.refresh_token)
        if expires_in:
            delta = datetime.timedelta(seconds=int(expires_in))
            self.token_expiry = delta + client._UTCNOW()
        else:
            self.token_expiry = None
        self.id_token_jwt = id_token
        self.id_token = (
            client._extract_id_token(id_token) if id_token else None)

        self.invalid = False
        if self.store:
            self.store.locked_put(self)
