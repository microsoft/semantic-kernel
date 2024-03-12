# -*- coding: utf-8 -*-
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Implementation of credentials that refreshes using the iamcredentials API."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import datetime

from oauth2client import client

from gslib.iamcredentials_api import IamcredentailsApi


class ImpersonationCredentials(client.OAuth2Credentials):
  _EXPIRY_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

  def __init__(self, service_account_id, scopes, credentials, logger):
    self._service_account_id = service_account_id
    self.api = IamcredentailsApi(logger, credentials)

    response = self.api.GenerateAccessToken(service_account_id, scopes)
    self.access_token = response.accessToken
    self.token_expiry = self._ConvertExpiryTime(response.expireTime)

    super(ImpersonationCredentials, self).__init__(self.access_token,
                                                   None,
                                                   None,
                                                   None,
                                                   self.token_expiry,
                                                   None,
                                                   None,
                                                   scopes=scopes)

  @property
  def service_account_id(self):
    return self._service_account_id

  def _refresh(self, http):
    # client.Oauth2Credentials converts scopes into a set, so we need to convert
    # back to a list before making the API request.
    response = self.api.GenerateAccessToken(self._service_account_id,
                                            list(self.scopes))
    self.access_token = response.accessToken
    self.token_expiry = self._ConvertExpiryTime(response.expireTime)

  def _ConvertExpiryTime(self, value):
    return datetime.datetime.strptime(value,
                                      ImpersonationCredentials._EXPIRY_FORMAT)
