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
"""google-auth p12 service account credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from google.auth import _helpers
from google.auth.crypt import base as crypt_base
from google.oauth2 import service_account

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding

import six

_DEFAULT_PASSWORD = 'notasecret'
_PYCA_CRYPTOGRAPHY_MIN_VERSION = '2.5'


class Error(exceptions.Error):
  """Base Error class for this module."""


class MissingRequiredFieldsError(Error):
  """Error when required fields are missing to construct p12 credentials."""


class MissingDependencyError(Error):
  """Error when missing a dependency to use p12 credentials."""


class PKCS12Signer(crypt_base.Signer, crypt_base.FromServiceAccountMixin):
  """Signer for a p12 service account key based on pyca/cryptography."""

  def __init__(self, key):
    self._key = key

  # Defined in the Signer interface, and is not useful for gcloud.
  @property
  def key_id(self):
    return None

  def sign(self, message):
    message = _helpers.to_bytes(message)
    from google.auth.crypt import _cryptography_rsa  # pylint: disable=g-import-not-at-top
    return self._key.sign(
        message,
        _cryptography_rsa._PADDING,  # pylint: disable=protected-access
        _cryptography_rsa._SHA256)  # pylint: disable=protected-access

  @classmethod
  def from_string(cls, key_strings, key_id=None):
    del key_id
    key_string, password = (_helpers.to_bytes(k) for k in key_strings)
    from cryptography.hazmat.primitives.serialization import pkcs12  # pylint: disable=g-import-not-at-top
    from cryptography.hazmat import backends  # pylint: disable=g-import-not-at-top
    key, _, _ = pkcs12.load_key_and_certificates(
        key_string, password, backend=backends.default_backend())
    return cls(key)


class PKCS12SignerPyOpenSSL(crypt_base.Signer,
                            crypt_base.FromServiceAccountMixin):
  """Signer for a p12 service account key based on pyOpenSSL."""

  def __init__(self, key):
    self._key = key

  # Defined in the Signer interface, and is not useful for gcloud.
  @property
  def key_id(self):
    return None

  def sign(self, message):
    message = _helpers.to_bytes(message)
    from OpenSSL import crypto  # pylint: disable=g-import-not-at-top
    return crypto.sign(self._key, message, six.ensure_str('sha256'))

  @classmethod
  def from_string(cls, key_strings, key_id=None):
    del key_id
    key_string, password = (_helpers.to_bytes(k) for k in key_strings)
    from OpenSSL import crypto  # pylint: disable=g-import-not-at-top
    key = crypto.load_pkcs12(key_string, password).get_privatekey()
    return cls(key)


class Credentials(service_account.Credentials):
  """google-auth service account credentials using p12 keys.

  p12 keys are not supported by the google-auth service account credentials.
  gcloud uses oauth2client to support p12 key users. Since oauth2client was
  deprecated and bundling it is security concern, we decided to support p12
  in gcloud codebase. We prefer not adding it to the google-auth library
  because p12 is not supported from the beginning by google-auth. GCP strongly
  suggests users to use the JSON format. gcloud has to support it to not
  break users.

  oauth2client uses PyOpenSSL to handle p12 keys. PyOpenSSL deprecated
  p12 support from version 20.0.0 and encourages to use pyca/cryptography for
  anything other than TLS connections. We should build the p12 support on
  pyca/cryptography. Otherwise, newer PyOpenSSL may remove p12 support and
  break p12 key users. The PyOpenSSL is used as a fallback to avoid breaking
  existing p12 users. Even though PyOpenSSL depends on pyca/cryptography and
  users who installed PyOpenSSL should have also installed pyca/cryptography,
  the pyca/cryptography may be older than version 2.5 which is the minimum
  required version.
  """

  _REQUIRED_FIELDS = ('service_account_email', 'token_uri', 'scopes')

  @property
  def private_key_pkcs12(self):
    return self._private_key_pkcs12

  @property
  def private_key_password(self):
    return self._private_key_password

  @classmethod
  def from_service_account_pkcs12_keystring(cls,
                                            key_string,
                                            password=None,
                                            **kwargs):
    password = password or _DEFAULT_PASSWORD
    try:
      signer = PKCS12Signer.from_string((key_string, password))
    except ImportError:
      log.debug(
          'pyca/cryptography is not available or the version is < {}. Fall '
          'back to using OpenSSL.'.format(_PYCA_CRYPTOGRAPHY_MIN_VERSION))
      signer = PKCS12SignerPyOpenSSL.from_string((key_string, password))

    missing_fields = [f for f in cls._REQUIRED_FIELDS if f not in kwargs]
    if missing_fields:
      raise MissingRequiredFieldsError('Missing fields: {}.'.format(
          ', '.join(missing_fields)))
    creds = cls(signer, **kwargs)
    # saving key_string and password is necessary because gcloud caches
    # credentials and re-construct it during runtime. Without them, we cannot
    # re-construct it.
    # pylint: disable=protected-access
    creds._private_key_pkcs12 = key_string
    creds._private_key_password = password
    # pylint: enable=protected-access
    return creds


def CreateP12ServiceAccount(key_string, password=None, **kwargs):
  """Creates a service account from a p12 key and handles import errors."""
  log.warning('.p12 service account keys are not recommended unless it is '
              'necessary for backwards compatibility. Please switch to '
              'a newer .json service account key for this account.')

  try:
    return Credentials.from_service_account_pkcs12_keystring(
        key_string, password, **kwargs)
  except ImportError:
    if not encoding.GetEncodedValue(os.environ, 'CLOUDSDK_PYTHON_SITEPACKAGES'):
      raise MissingDependencyError(
          ('pyca/cryptography is not available. Please install or upgrade it '
           'to a version >= {} and set the environment variable '
           'CLOUDSDK_PYTHON_SITEPACKAGES to 1. If that does not work, see '
           'https://developers.google.com/cloud/sdk/crypto for details '
           'or consider using .json private key instead.'
          ).format(_PYCA_CRYPTOGRAPHY_MIN_VERSION))
    else:
      raise MissingDependencyError(
          ('pyca/cryptography is not available or the version is < {}. '
           'Please install or upgrade it to a newer version. See '
           'https://developers.google.com/cloud/sdk/crypto for details '
           'or consider using .json private key instead.'
          ).format(_PYCA_CRYPTOGRAPHY_MIN_VERSION))
