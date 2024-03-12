# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Manages logic for external accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import introspect as c_introspect
from googlecloudsdk.core.util import files

_EXTERNAL_ACCOUNT_TYPE = 'external_account'


class Error(exceptions.Error):
  """Errors raised by this module."""


class BadCredentialFileException(Error):
  """Raised when file cannot be read."""


class BadCredentialJsonFileException(Error):
  """Raised when the JSON file is in an invalid format."""


def GetExternalAccountCredentialsConfig(filename):
  """Returns the JSON content if the file corresponds to an external account.

  This function is useful when the content of a file need to be inspected first
  before determining how to handle it. More specifically, it would check a
  config file contains an external account cred and return its content which can
  then be used with CredentialsFromAdcDictGoogleAuth (if the contents
  correspond to an external account cred) to avoid having to open the file
  twice.

  Args:
    filename (str): The filepath to the ADC file representing an external
      account credentials.

  Returns:
    Optional(Mapping): The JSON content if the configuration represents an
      external account. Otherwise None is returned.

  Raises:
    BadCredentialFileException: If JSON parsing of the file fails.
  """

  content = files.ReadFileContents(filename)
  try:
    content_json = json.loads(content)
  except ValueError as e:
    # File has to be in JSON format.
    raise BadCredentialFileException('Could not read json file {0}: {1}'.format(
        filename, e))
  if IsExternalAccountConfig(content_json):
    return content_json
  else:
    return None


def IsExternalAccountConfig(content_json):
  """Returns whether a JSON content corresponds to an external account cred."""
  return (content_json or {}).get('type') == _EXTERNAL_ACCOUNT_TYPE


def CredentialsFromAdcDictGoogleAuth(external_config):
  """Creates external account creds from a dict of application default creds.

  Args:
    external_config (Mapping): The configuration dictionary representing the
      credentials. This is loaded from the ADC file typically.

  Returns:
    google.auth.external_account.Credentials: The initialized external account
      credentials.

  Raises:
    BadCredentialJsonFileException: If the config format is invalid.
    googlecloudsdk.core.credentials.creds.InvalidCredentialsError: If the
      provided configuration is invalid or unsupported.
  """
  if ('type' not in external_config or
      external_config['type'] != _EXTERNAL_ACCOUNT_TYPE):
    raise BadCredentialJsonFileException(
        'The provided credentials configuration is not in a valid format.')

  return c_creds.FromJsonGoogleAuth(json.dumps(external_config))


def GetExternalAccountId(creds):
  """Returns the account identifier corresponding to the external account creds.

  Args:
    creds (google.auth.credentials.Credentials): The credentials whose account
      ID is to be returned.

  Returns:
    Optional(str): The corresponding account ID, or None if the credentials are
      not external_account credentials.
  """

  if (c_creds.IsExternalAccountCredentials(creds) or
      c_creds.IsExternalAccountUserCredentials(creds) or
      c_creds.IsExternalAccountAuthorizedUserCredentials(creds)):
    return (getattr(creds, 'service_account_email', None) or
            c_introspect.GetExternalAccountId(creds))
  return None
