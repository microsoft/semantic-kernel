# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""User errors raised by auth commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class AuthenticationError(exceptions.Error):
  """Raised for errors reported by Oauth2client library."""


class InvalidCredentialsError(exceptions.Error):
  """Raised if credentials are not usable."""


class WrongAccountError(exceptions.Error):
  """Raised when credential account does not match expected account."""


class GitCredentialHelperError(exceptions.Error):
  """Raised for issues related to passing auth credentials to Git."""


class InvalidIdentityTokenError(exceptions.Error):
  """Raised when identity token of credential is None."""


class WrongAccountTypeError(exceptions.Error):
  """Raised when audiences are specified but account type is not service account."""


class GCEIdentityTokenError(exceptions.Error):
  """Raised when request for GCE ID token is wrong."""
