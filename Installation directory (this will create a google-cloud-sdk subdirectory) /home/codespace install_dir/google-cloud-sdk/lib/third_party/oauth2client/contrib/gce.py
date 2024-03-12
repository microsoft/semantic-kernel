# Copyright 2014 Google Inc. All rights reserved.
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

"""Utilities for Google Compute Engine

Utilities for making it easier to use OAuth 2.0 on Google Compute Engine.
"""

import logging
import warnings

import httplib2

from oauth2client import client
from oauth2client.contrib import _metadata


__author__ = 'jcgregorio@google.com (Joe Gregorio)'

logger = logging.getLogger(__name__)

_SCOPES_WARNING = """\
You have requested explicit scopes to be used with a GCE service account.
Using this argument will have no effect on the actual scopes for tokens
requested. These scopes are set at VM instance creation time and
can't be overridden in the request.
"""


class AppAssertionCredentials(client.AssertionCredentials):
    """Credentials object for Compute Engine Assertion Grants

    This object will allow a Compute Engine instance to identify itself to
    Google and other OAuth 2.0 servers that can verify assertions. It can be
    used for the purpose of accessing data stored under an account assigned to
    the Compute Engine instance itself.

    This credential does not require a flow to instantiate because it
    represents a two legged flow, and therefore has all of the required
    information to generate and refresh its own access tokens.

    Note that :attr:`service_account_email` and :attr:`scopes`
    will both return None until the credentials have been refreshed.
    To check whether credentials have previously been refreshed use
    :attr:`invalid`.
    """

    def __init__(self, email=None, *args, **kwargs):
        """Constructor for AppAssertionCredentials

        Args:
            email: an email that specifies the service account to use.
                   Only necessary if using custom service accounts
                   (see https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#createdefaultserviceaccount).
        """
        if 'scopes' in kwargs:
            warnings.warn(_SCOPES_WARNING)
            kwargs['scopes'] = None

        # Assertion type is no longer used, but still in the
        # parent class signature.
        super(AppAssertionCredentials, self).__init__(None, *args, **kwargs)

        self.service_account_email = email
        self.scopes = None
        self.invalid = True

    @classmethod
    def from_json(cls, json_data):
        raise NotImplementedError(
            'Cannot serialize credentials for GCE service accounts.')

    def to_json(self):
        raise NotImplementedError(
            'Cannot serialize credentials for GCE service accounts.')

    def retrieve_scopes(self, http):
        """Retrieves the canonical list of scopes for this access token.

        Overrides client.Credentials.retrieve_scopes. Fetches scopes info
        from the metadata server.

        Args:
            http: httplib2.Http, an http object to be used to make the refresh
                  request.

        Returns:
            A set of strings containing the canonical list of scopes.
        """
        self._retrieve_info(http.request)
        return self.scopes

    def _retrieve_info(self, http_request):
        """Validates invalid service accounts by retrieving service account info.

        Args:
            http_request: callable, a callable that matches the method
                          signature of httplib2.Http.request, used to make the
                          request to the metadata server
        """
        if self.invalid:
            info = _metadata.get_service_account_info(
                http_request,
                service_account=self.service_account_email or 'default')
            self.invalid = False
            self.service_account_email = info['email']
            self.scopes = info['scopes']

    def _refresh(self, http_request):
        """Refreshes the access_token.

        Skip all the storage hoops and just refresh using the API.

        Args:
            http_request: callable, a callable that matches the method
                          signature of httplib2.Http.request, used to make
                          the refresh request.

        Raises:
            HttpAccessTokenRefreshError: When the refresh fails.
        """
        try:
            self._retrieve_info(http_request)
            self.access_token, self.token_expiry = _metadata.get_token(
                http_request, service_account=self.service_account_email)
        except httplib2.HttpLib2Error as e:
            raise client.HttpAccessTokenRefreshError(str(e))

    @property
    def serialization_data(self):
        raise NotImplementedError(
            'Cannot serialize credentials for GCE service accounts.')

    def create_scoped_required(self):
        return False

    def sign_blob(self, blob):
        """Cryptographically sign a blob (of bytes).

        This method is provided to support a common interface, but
        the actual key used for a Google Compute Engine service account
        is not available, so it can't be used to sign content.

        Args:
            blob: bytes, Message to be signed.

        Raises:
            NotImplementedError, always.
        """
        raise NotImplementedError(
            'Compute Engine service accounts cannot sign blobs')
