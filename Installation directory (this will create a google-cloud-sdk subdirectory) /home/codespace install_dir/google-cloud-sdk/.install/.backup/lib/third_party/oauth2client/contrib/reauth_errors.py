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
"""A module that provides rapt authentication errors."""


class ReauthError(Exception):
    """Base exception for reauthentication."""
    pass


class ReauthUnattendedError(ReauthError):
    """An exception for when reauth cannot be answered."""

    def __init__(self):
        super(ReauthUnattendedError, self).__init__(
            'Reauthentication challenge could not be answered because you are '
            'not in an interactive session.')


class ReauthFailError(ReauthError):
    """An exception for when reauth failed."""

    def __init__(self):
        super(ReauthFailError, self).__init__(
            'Reauthentication challenge failed.')


class ReauthAPIError(ReauthError):
    """An exception for when reauth API returned something we can't handle."""

    def __init__(self, api_error):
        super(ReauthAPIError, self).__init__(
            'Reauthentication challenge failed due to API error: {0}.'.format(
                api_error))


class ReauthAccessTokenRefreshError(ReauthError):
    """An exception for when we can't get an access token for reauth."""

    def __init__(self):
        super(ReauthAccessTokenRefreshError, self).__init__(
            'Failed to get an access token for reauthentication.')


class ReauthSamlLoginRequiredError(ReauthError):
    """An exception for when web login is required to complete reauth.

    This applies to SAML users who are required to login through their IDP to
    complete reauth.
    """

    def __init__(self):
        super(ReauthSamlLoginRequiredError, self).__init__(
            'SAML login is required for the current account to complete '
            'reauthentication.')
