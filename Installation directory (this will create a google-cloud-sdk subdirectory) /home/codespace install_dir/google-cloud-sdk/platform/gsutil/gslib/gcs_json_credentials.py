# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Credentials logic for JSON CloudApi implementation."""

# This module duplicates some logic in third_party gcs_oauth2_boto_plugin
# because apitools credentials lib has its own mechanisms for file-locking
# and credential storage.  As such, it doesn't require most of the
# gcs_oauth2_boto_plugin logic.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import logging
import os
import io
import six
import traceback

# pylint: disable=g-bad-import-order
from apitools.base.py import credentials_lib
from apitools.base.py import exceptions as apitools_exceptions
from boto import config
from gslib.cred_types import CredTypes
from gslib.exception import CommandException
from gslib.impersonation_credentials import ImpersonationCredentials
from gslib.no_op_credentials import NoOpCredentials
from gslib.utils import constants
from gslib.utils import system_util
from gslib.utils.boto_util import GetFriendlyConfigFilePaths
from gslib.utils.boto_util import GetCredentialStoreFilename
from gslib.utils.boto_util import GetGceCredentialCacheFilename
from gslib.utils.boto_util import GetGcsJsonApiVersion
from gslib.utils.constants import UTF8
from gslib.utils.wrapped_credentials import WrappedCredentials
import oauth2client
from oauth2client.client import HAS_CRYPTO
from oauth2client.contrib import devshell
from oauth2client.service_account import ServiceAccountCredentials
from google_reauth import reauth_creds
from oauth2client.contrib import multiprocess_file_storage

from six import BytesIO

DEFAULT_GOOGLE_OAUTH2_PROVIDER_AUTHORIZATION_URI = (
    'https://accounts.google.com/o/oauth2/auth')
DEFAULT_GOOGLE_OAUTH2_PROVIDER_TOKEN_URI = (
    'https://oauth2.googleapis.com/token')

DEFAULT_SCOPES = [
    constants.Scopes.CLOUD_PLATFORM,
    constants.Scopes.CLOUD_PLATFORM_READ_ONLY,
    constants.Scopes.FULL_CONTROL,
    constants.Scopes.READ_ONLY,
    constants.Scopes.READ_WRITE,
]

GOOGLE_OAUTH2_DEFAULT_FILE_PASSWORD = 'notasecret'


def GetCredentialStoreKey(credentials, api_version):
  """Disambiguates a credential for caching in a credential store.

  Different credential types have different fields that identify them.  This
  function assembles relevant information in a string to be used as the key for
  accessing a credential.  Note that in addition to uniquely identifying the
  entity to which a credential corresponds, we must differentiate between two or
  more of that entity's credentials that have different attributes such that the
  credentials should not be treated as interchangeable, e.g. if they target
  different API versions (happens for developers targeting different test
  environments), have different private key IDs (for service account JSON
  keyfiles), or target different provider token (refresh) URIs.

  Args:
    credentials: An OAuth2Credentials object.
    api_version: JSON API version being used.

  Returns:
    A string that can be used as the key to identify a credential, e.g.
    "v1-909320924072.apps.googleusercontent.com-1/rEfrEshtOkEn-https://..."
  """
  # Note: We don't include the scopes as part of the key. For a user credential
  # object, we always construct it with manually added scopes that are necessary
  # to negotiate reauth challenges - those scopes don't necessarily correspond
  # to the scopes the refresh token was created with. We avoid key name
  # mismatches for the same refresh token by not including scopes in the key
  # string.
  key_parts = [api_version]
  if isinstance(credentials, devshell.DevshellCredentials):
    key_parts.append(credentials.user_email)
  elif isinstance(credentials, ServiceAccountCredentials):
    # pylint: disable=protected-access
    key_parts.append(credentials._service_account_email)
    if getattr(credentials, '_private_key_id', None):  # JSON keyfile.
      # Differentiate between two different JSON keyfiles for the same service
      # account.
      key_parts.append(credentials._private_key_id)
    elif getattr(credentials, '_private_key_pkcs12', None):  # P12 keyfile
      # Use a prefix of the Base64-encoded PEM string to differentiate it from
      # others. Using a prefix of reasonable length prevents the key from being
      # unnecessarily large, and the likelihood of having two PEM strings with
      # the same prefixes is sufficiently low.
      key_parts.append(base64.b64encode(credentials._private_key_pkcs12)[:20])
    # pylint: enable=protected-access
  elif isinstance(credentials, oauth2client.client.OAuth2Credentials):
    if credentials.client_id and credentials.client_id != 'null':
      key_parts.append(credentials.client_id)
    else:
      key_parts.append('noclientid')
    key_parts.append(credentials.refresh_token or 'norefreshtoken')

  # If a cached credential is targeting provider token URI 'A' for token refresh
  # requests, then the user changes their boto file or private key file to
  # target URI 'B', we don't want to treat the cached and the new credential as
  # interchangeable.  This applies for all credentials that store a token URI.
  if getattr(credentials, 'token_uri', None):
    key_parts.append(credentials.token_uri)
  key_parts = [six.ensure_text(part) for part in key_parts]
  return '-'.join(key_parts)


def SetUpJsonCredentialsAndCache(api, logger, credentials=None):
  """Helper to ensure each GCS API client shares the same credentials."""
  api.credentials = (credentials or _CheckAndGetCredentials(logger) or
                     NoOpCredentials())

  # Notify the user that impersonation credentials are in effect.
  if isinstance(api.credentials, ImpersonationCredentials):
    logger.warn(
        'WARNING: This command is using service account impersonation. All '
        'API calls will be executed as [%s].', _GetImpersonateServiceAccount())

  # Set credential cache so that we don't have to get a new access token for
  # every call we make. All GCS APIs use the same credentials as the JSON API,
  # so we use its version in the key for caching access tokens.
  credential_store_key = (GetCredentialStoreKey(api.credentials,
                                                GetGcsJsonApiVersion()))
  api.credentials.set_store(
      multiprocess_file_storage.MultiprocessFileStorage(
          GetCredentialStoreFilename(), credential_store_key))
  # The cached entry for this credential often contains more context than what
  # we can construct from boto config attributes (e.g. for a user credential,
  # the cached version might also contain a RAPT token and expiry info).
  # Prefer the cached credential if present.
  cached_cred = None
  if not isinstance(api.credentials, NoOpCredentials):
    # A NoOpCredentials object doesn't actually have a store attribute.
    cached_cred = api.credentials.store.get()
  # As of gsutil 4.31, we never use the OAuth2Credentials class for
  # credentials directly; rather, we use subclasses (user credentials were
  # the only ones left using it, but they now use
  # Oauth2WithReauthCredentials).  If we detect that a cached credential is
  # an instance of OAuth2Credentials and not a subclass of it (as might
  # happen when transitioning to version v4.31+), we don't fetch it from the
  # cache. This results in our new-style credential being refreshed and
  # overwriting the old credential cache entry in our credstore.
  if (cached_cred and
      type(cached_cred) != oauth2client.client.OAuth2Credentials):
    api.credentials = cached_cred


def _CheckAndGetCredentials(logger):
  """Returns credentials from the configuration file, if any are present.

  Args:
    logger: logging.Logger instance for outputting messages.

  Returns:
    OAuth2Credentials object if any valid ones are found, otherwise None.
  """
  configured_cred_types = []
  failed_cred_type = None
  try:
    if _HasOauth2UserAccountCreds():
      configured_cred_types.append(CredTypes.OAUTH2_USER_ACCOUNT)
    if _HasOauth2ServiceAccountCreds():
      configured_cred_types.append(CredTypes.OAUTH2_SERVICE_ACCOUNT)
    if len(configured_cred_types) > 1:
      # We only allow one set of configured credentials. Otherwise, we're
      # choosing one arbitrarily, which can be very confusing to the user
      # (e.g., if only one is authorized to perform some action) and can
      # also mask errors.
      # Because boto merges config files, GCE credentials show up by default
      # for GCE VMs. We don't want to fail when a user creates a boto file
      # with their own credentials, so in this case we'll use the OAuth2
      # user credentials.
      raise CommandException(
          ('You have multiple types of configured credentials (%s), which is '
           'not supported. One common way this happens is if you run gsutil '
           'config to create credentials and later run gcloud auth, and '
           'create a second set of credentials. Your boto config path is: '
           '%s. For more help, see "gsutil help creds".') %
          (configured_cred_types, GetFriendlyConfigFilePaths()))

    failed_cred_type = CredTypes.OAUTH2_USER_ACCOUNT
    user_creds = _GetOauth2UserAccountCredentials()
    failed_cred_type = CredTypes.OAUTH2_SERVICE_ACCOUNT
    service_account_creds = _GetOauth2ServiceAccountCredentials()
    failed_cred_type = CredTypes.EXTERNAL_ACCOUNT
    external_account_creds = _GetExternalAccountCredentials()
    failed_cred_type = CredTypes.EXTERNAL_ACCOUNT_AUTHORIZED_USER
    external_account_authorized_user_creds = _GetExternalAccountAuthorizedUserCredentials(
    )
    failed_cred_type = CredTypes.GCE
    gce_creds = _GetGceCreds()
    failed_cred_type = CredTypes.DEVSHELL
    devshell_creds = _GetDevshellCreds()

    creds = user_creds or service_account_creds or gce_creds or external_account_creds or external_account_authorized_user_creds or devshell_creds

    # Use one of the above credential types to impersonate, if configured.
    if _HasImpersonateServiceAccount() and creds:
      failed_cred_type = CredTypes.IMPERSONATION
      return _GetImpersonationCredentials(creds, logger)
    else:
      return creds

  except Exception as e:
    # If we didn't actually try to authenticate because there were multiple
    # types of configured credentials, don't emit this warning.
    if failed_cred_type:
      if logger.isEnabledFor(logging.DEBUG):
        logger.debug(traceback.format_exc())
      # If impersonation fails, show the user the actual error, since we handle
      # errors in iamcredentials_api.
      if failed_cred_type == CredTypes.IMPERSONATION:
        raise e
      elif system_util.InvokedViaCloudSdk():
        logger.warn(
            'Your "%s" credentials are invalid. Please run\n'
            '  $ gcloud auth login', failed_cred_type)
      else:
        logger.warn(
            'Your "%s" credentials are invalid. For more help, see '
            '"gsutil help creds", or re-run the gsutil config command (see '
            '"gsutil help config").', failed_cred_type)

    # If there's any set of configured credentials, we'll fail if they're
    # invalid, rather than silently falling back to anonymous config (as
    # boto does). That approach leads to much confusion if users don't
    # realize their credentials are invalid.
    raise


def _GetProviderTokenUri():
  return config.get('OAuth2', 'provider_token_uri',
                    DEFAULT_GOOGLE_OAUTH2_PROVIDER_TOKEN_URI)


def _HasOauth2ServiceAccountCreds():
  return config.has_option('Credentials', 'gs_service_key_file')


def _HasOauth2UserAccountCreds():
  return config.has_option('Credentials', 'gs_oauth2_refresh_token')


def _HasGceCreds():
  return config.has_option('GoogleCompute', 'service_account')


def _HasImpersonateServiceAccount():
  return _GetImpersonateServiceAccount() not in (None, '')


def _GetExternalAccountCredentials():
  external_account_filename = config.get('Credentials',
                                         'gs_external_account_file', None)
  if not external_account_filename:
    return None

  return WrappedCredentials.for_external_account(external_account_filename)


def _GetExternalAccountAuthorizedUserCredentials():
  external_account_authorized_user_filename = config.get(
      'Credentials', 'gs_external_account_authorized_user_file', None)
  if not external_account_authorized_user_filename:
    return None

  return WrappedCredentials.for_external_account_authorized_user(
      external_account_authorized_user_filename)


def _GetImpersonateServiceAccount():
  return (constants.IMPERSONATE_SERVICE_ACCOUNT or config.get(
      'Credentials', 'gs_impersonate_service_account',
      os.environ.get('CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT')))


def _GetOauth2ServiceAccountCredentials():
  """Retrieves OAuth2 service account credentials for a private key file."""
  if not _HasOauth2ServiceAccountCreds():
    return

  provider_token_uri = _GetProviderTokenUri()
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
    # Key file is in JSON format.
    for json_entry in ('client_id', 'client_email', 'private_key_id',
                       'private_key'):
      if json_entry not in json_key_dict:
        raise Exception('The JSON private key file at %s '
                        'did not contain the required entry: %s' %
                        (private_key_filename, json_entry))
    return ServiceAccountCredentials.from_json_keyfile_dict(
        json_key_dict, scopes=DEFAULT_SCOPES, token_uri=provider_token_uri)
  else:
    # Key file is in P12 format.
    if HAS_CRYPTO:
      if not service_client_id:
        raise Exception('gs_service_client_id must be set if '
                        'gs_service_key_file is set to a .p12 key file')
      key_file_pass = config.get('Credentials', 'gs_service_key_file_password',
                                 GOOGLE_OAUTH2_DEFAULT_FILE_PASSWORD)
      # We use _from_p12_keyfile_contents to avoid reading the key file
      # again unnecessarily.
      try:
        return ServiceAccountCredentials.from_p12_keyfile_buffer(
            service_client_id,
            BytesIO(private_key),
            private_key_password=key_file_pass,
            scopes=DEFAULT_SCOPES,
            token_uri=provider_token_uri)
      except Exception as e:
        raise Exception(
            'OpenSSL unable to parse PKCS 12 key {}.'
            'Please verify key integrity. Error message:\n{}'.format(
                private_key_filename, str(e)))


def _GetOauth2UserAccountCredentials():
  """Retrieves OAuth2 service account credentials for a refresh token."""
  if not _HasOauth2UserAccountCreds():
    return

  provider_token_uri = _GetProviderTokenUri()
  gsutil_client_id, gsutil_client_secret = (
      system_util.GetGsutilClientIdAndSecret())
  client_id = config.get('OAuth2', 'client_id',
                         os.environ.get('OAUTH2_CLIENT_ID', gsutil_client_id))
  client_secret = config.get(
      'OAuth2', 'client_secret',
      os.environ.get('OAUTH2_CLIENT_SECRET', gsutil_client_secret))
  # Note that these scopes don't necessarily correspond to the refresh token
  # being used. This list is is used for obtaining the RAPT in the reauth flow,
  # to determine which challenges should be used.
  scopes_for_reauth_challenge = [
      constants.Scopes.CLOUD_PLATFORM, constants.Scopes.REAUTH
  ]
  return reauth_creds.Oauth2WithReauthCredentials(
      None,  # access_token
      client_id,
      client_secret,
      config.get('Credentials', 'gs_oauth2_refresh_token'),
      None,  # token_expiry
      provider_token_uri,
      None,  # user_agent
      scopes=scopes_for_reauth_challenge)


def _GetGceCreds():
  if not _HasGceCreds():
    return

  try:
    return credentials_lib.GceAssertionCredentials(
        service_account_name=config.get('GoogleCompute', 'service_account',
                                        'default'),
        cache_filename=GetGceCredentialCacheFilename())
  except apitools_exceptions.ResourceUnavailableError as e:
    if 'service account' in str(e) and 'does not exist' in str(e):
      return None
    raise


def _GetDevshellCreds():
  try:
    return devshell.DevshellCredentials()
  except devshell.NoDevshellServer:
    return None
  except:
    raise


def _GetImpersonationCredentials(credentials, logger):
  """Retrieves temporary credentials impersonating a service account"""

  # We don't use impersoned credentials to impersonate.
  if isinstance(credentials, ImpersonationCredentials):
    return

  return ImpersonationCredentials(_GetImpersonateServiceAccount(),
                                  [constants.Scopes.CLOUD_PLATFORM],
                                  credentials, logger)
