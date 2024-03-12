# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utilities to manage credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import base64
import copy
import datetime
import enum
import hashlib
import json
import os
import sqlite3

from google.auth import compute_engine as google_auth_compute_engine
from google.auth import credentials as google_auth_creds
from google.auth import exceptions as google_auth_exceptions
from google.auth import external_account as google_auth_external_account
from google.auth import external_account_authorized_user as google_auth_external_account_authorized_user

from google.auth import impersonated_credentials as google_auth_impersonated
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.credentials import exceptions as c_exceptions
from googlecloudsdk.core.credentials import introspect as c_introspect
from googlecloudsdk.core.util import files
from oauth2client import client
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce
import six

ADC_QUOTA_PROJECT_FIELD_NAME = 'quota_project_id'

_REVOKE_URI = 'https://accounts.google.com/o/oauth2/revoke'

UNKNOWN_CREDS_NAME = 'unknown'
USER_ACCOUNT_CREDS_NAME = 'authorized_user'
SERVICE_ACCOUNT_CREDS_NAME = 'service_account'
P12_SERVICE_ACCOUNT_CREDS_NAME = 'service_account_p12'
DEVSHELL_CREDS_NAME = 'devshell'
GCE_CREDS_NAME = 'gce'
IMPERSONATED_ACCOUNT_CREDS_NAME = 'impersonated_account'
EXTERNAL_ACCOUNT_CREDS_NAME = 'external_account'
EXTERNAL_ACCOUNT_USER_CREDS_NAME = 'external_account_user'
EXTERNAL_ACCOUNT_AUTHORIZED_USER_CREDS_NAME = 'external_account_authorized_user'


class Error(exceptions.Error):
  """Exceptions for this module."""


class UnknownCredentialsType(Error):
  """An error for when we fail to determine the type of the credentials."""


class InvalidCredentialsError(Error):
  """Exception for when the provided credentials are invalid or unsupported."""


class CredentialFileSaveError(Error):
  """An error for when we fail to save a credential file."""


class ADCError(Error):
  """An error when processing application default credentials."""


def IsOauth2ClientCredentials(creds):
  return isinstance(creds, client.OAuth2Credentials)


def IsGoogleAuthCredentials(creds):
  return isinstance(creds, google_auth_creds.Credentials)


def IsGoogleAuthGceCredentials(creds):
  return isinstance(creds, google_auth_compute_engine.Credentials)


def _IsUserAccountCredentialsOauth2client(creds):
  if CredentialType.FromCredentials(creds).is_user:
    return True
  if c_devshell.IsDevshellEnvironment():
    return CredentialType.FromCredentials(creds) == CredentialType.GCE
  else:
    return False


def _IsUserAccountCredentialsGoogleAuth(creds):
  if CredentialTypeGoogleAuth.FromCredentials(creds).is_user:
    return True
  if c_devshell.IsDevshellEnvironment():
    return CredentialTypeGoogleAuth.FromCredentials(
        creds) == CredentialTypeGoogleAuth.GCE
  else:
    return False


def IsUserAccountCredentials(creds):
  if IsOauth2ClientCredentials(creds):
    return _IsUserAccountCredentialsOauth2client(creds)
  else:
    return _IsUserAccountCredentialsGoogleAuth(creds)


def IsOauth2clientP12AccountCredentials(creds):
  return (CredentialType.FromCredentials(creds) ==
          CredentialType.P12_SERVICE_ACCOUNT)


def IsServiceAccountCredentials(creds):
  if IsOauth2ClientCredentials(creds):
    cred_type = CredentialType.FromCredentials(creds)
    return cred_type in (CredentialType.SERVICE_ACCOUNT,
                         CredentialType.P12_SERVICE_ACCOUNT)
  else:
    cred_type = CredentialTypeGoogleAuth.FromCredentials(creds)
    return cred_type in (CredentialTypeGoogleAuth.SERVICE_ACCOUNT,
                         CredentialTypeGoogleAuth.P12_SERVICE_ACCOUNT)


def IsExternalAccountCredentials(creds):
  if IsGoogleAuthCredentials(creds):
    return (CredentialTypeGoogleAuth.FromCredentials(creds) ==
            CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT)
  return False


def IsExternalAccountUserCredentials(creds):
  if IsGoogleAuthCredentials(creds):
    return (CredentialTypeGoogleAuth.FromCredentials(creds) ==
            CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_USER)
  return False


def IsExternalAccountAuthorizedUserCredentials(creds):
  if IsGoogleAuthCredentials(creds):
    return (CredentialTypeGoogleAuth.FromCredentials(creds) ==
            CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_AUTHORIZED_USER)
  return False


def IsImpersonatedAccountCredentials(creds):
  if IsGoogleAuthCredentials(creds):
    return (CredentialTypeGoogleAuth.FromCredentials(creds) ==
            CredentialTypeGoogleAuth.IMPERSONATED_ACCOUNT)
  return False


def HasDefaultUniverseDomain(credentials):
  """Check if the given credential has default universe domain.

  For google-auth credential, we check its universe_domain property. The
  deprecated oauth2client credentials only work in default universe domain so
  we return True (Note that they are no longer used in gcloud, but not yet
  removed from the code base).

  Args:
    credentials: google.auth.credentials.Credentials or
      client.OAuth2Credentials, the credentials to be checked.

  Returns:
    bool, Whether or not the given credential has default universe domain.
  """
  if IsGoogleAuthCredentials(credentials):
    return (
        credentials.universe_domain
        == properties.VALUES.core.universe_domain.default
    )
  return True


def GetEffectiveTokenUri(cred_json, key='token_uri'):
  if properties.VALUES.auth.token_host.IsExplicitlySet():
    return properties.VALUES.auth.token_host.Get()
  if cred_json.get(key):
    return cred_json.get(key)
  return properties.VALUES.auth.DEFAULT_TOKEN_HOST


def UseSelfSignedJwt(creds):
  """Check if self signed jwt should be used.

  Only use self signed jwt for google-auth service account creds, and only when
  service_account_use_self_signed_jwt property is true or the universe is not
  the default one.

  Args:
    creds: google.auth.credentials.Credentials, The credentials to check if
      self signed jwt should be used.

  Returns:
    bool, Whether or not self signed jwt should be used.
  """
  cred_type = CredentialTypeGoogleAuth.FromCredentials(creds)

  if cred_type != CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    return False
  if creds.universe_domain != properties.VALUES.core.universe_domain.default:
    return True
  if properties.VALUES.auth.service_account_use_self_signed_jwt.GetBool():
    return True
  if not properties.IsDefaultUniverse():
    return True
  return False


def EnableSelfSignedJwtIfApplicable(creds):
  if UseSelfSignedJwt(creds):
    creds._always_use_jwt_access = True  # pylint: disable=protected-access
    creds._create_self_signed_jwt(None)  # pylint: disable=protected-access


def WithAccount(creds, account):
  """Add user account to credential.

  The user account field is used to determine ADC caching.
  Only User Account credential types will be modified.

  Args:
    creds: google.auth.credentials.Credentials, The credentials to add the
      account field
    account: str, the authorized user email

  Returns:
    google_auth_creds.Credential
  """
  cred_type = CredentialTypeGoogleAuth.FromCredentials(creds)
  if cred_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    creds = creds.with_account(account)
  return creds


@six.add_metaclass(abc.ABCMeta)
class CredentialStore(object):
  """Abstract definition of credential store."""

  @abc.abstractmethod
  def GetAccounts(self):
    """Get all accounts that have credentials stored for the CloudSDK.

    Returns:
      {str}, Set of accounts.
    """
    return NotImplemented

  @abc.abstractmethod
  def Load(self, account_id):
    return NotImplemented

  @abc.abstractmethod
  def Store(self, account_id, credentials):
    return NotImplemented

  @abc.abstractmethod
  def Remove(self, account_id):
    return NotImplemented

_CREDENTIAL_TABLE_NAME = 'credentials'


class _SqlCursor(object):
  """Context manager to access sqlite store."""

  def __init__(self, store_file):
    self._store_file = store_file
    self._connection = None
    self._cursor = None

  def __enter__(self):
    self._connection = sqlite3.connect(
        self._store_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # Use autocommit mode.
        check_same_thread=True  # Only creating thread may use the connection.
    )
    # Wait up to 1 second for any locks to clear up.
    # https://sqlite.org/pragma.html#pragma_busy_timeout
    self._connection.execute('PRAGMA busy_timeout = 1000')
    self._cursor = self._connection.cursor()
    return self

  def __exit__(self, exc_type, unused_value, unused_traceback):
    if not exc_type:
      # Don't try to commit if exception is in progress.
      self._connection.commit()
    self._connection.close()

  def Execute(self, *args):
    return self._cursor.execute(*args)


class SqliteCredentialStore(CredentialStore):
  """Sqllite backed credential store."""

  def __init__(self, store_file):
    self._cursor = _SqlCursor(store_file)
    self._Execute(
        'CREATE TABLE IF NOT EXISTS "{}" '
        '(account_id TEXT PRIMARY KEY, value BLOB)'
        .format(_CREDENTIAL_TABLE_NAME))

  def _Execute(self, *args):
    with self._cursor as cur:
      return cur.Execute(*args)

  def GetAccounts(self):
    with self._cursor as cur:
      return set(key[0] for key in cur.Execute(
          'SELECT account_id FROM "{}" ORDER BY rowid'
          .format(_CREDENTIAL_TABLE_NAME)))

  def GetAccountsWithUniverseDomain(self):
    """Get all accounts and their corresponding universe domains.

    Returns:
      dict[str, str], A dictionary where the key is the account and the value is
        the universe domain.
    """
    accounts_dict = {}
    with self._cursor as cur:
      for account_id_and_cred_json_tuple in cur.Execute(
          'SELECT account_id, value FROM "{}" ORDER BY rowid'.format(
              _CREDENTIAL_TABLE_NAME
          )
      ):
        account_id = account_id_and_cred_json_tuple[0]
        cred_json_string = account_id_and_cred_json_tuple[1]
        cred_json = json.loads(cred_json_string)
        accounts_dict[account_id] = cred_json.get(
            'universe_domain', properties.VALUES.core.universe_domain.default
        )
    return accounts_dict

  def Load(self, account_id, use_google_auth=True):
    with self._cursor as cur:
      item = cur.Execute(
          'SELECT value FROM "{}" WHERE account_id = ?'
          .format(_CREDENTIAL_TABLE_NAME), (account_id,)).fetchone()
    if item is None:
      return None

    if use_google_auth:
      creds = FromJsonGoogleAuth(item[0])
      universe_domain_from_property = (
          properties.VALUES.core.universe_domain.Get()
      )
      if creds.universe_domain != universe_domain_from_property:
        raise InvalidCredentialsError(
            'Your credentials are from "%(universe_from_cred)s", but your'
            ' [core/universe_domain] property is set to'
            ' "%(universe_from_property)s". Update your active account to an'
            ' account from "%(universe_from_property)s" or update the'
            ' [core/universe_domain] property to "%(universe_from_cred)s".'
            % {
                'universe_from_cred': creds.universe_domain,
                'universe_from_property': universe_domain_from_property,
            }
        )
      return creds

    return FromJson(item[0])

  def Store(self, account_id, credentials):
    """Stores the input credentials to the record of account_id in the cache.

    Args:
      account_id: string, the account ID of the input credentials.
      credentials: google.auth.credentials.Credentials or
        client.OAuth2Credentials, the credentials to be stored.
    """
    if IsOauth2ClientCredentials(credentials):
      value = ToJson(credentials)
    else:
      value = ToJsonGoogleAuth(credentials)
    self._Execute(
        'REPLACE INTO "{}" (account_id, value) VALUES (?,?)'
        .format(_CREDENTIAL_TABLE_NAME), (account_id, value))

  def Remove(self, account_id):
    self._Execute(
        'DELETE FROM "{}" WHERE account_id = ?'
        .format(_CREDENTIAL_TABLE_NAME), (account_id,))


_ACCESS_TOKEN_TABLE = 'access_tokens'


class AccessTokenCache(object):
  """Sqlite implementation of for access token cache."""

  def __init__(self, store_file):
    self._cursor = _SqlCursor(store_file)
    self._Execute(
        'CREATE TABLE IF NOT EXISTS "{}" '
        '(account_id TEXT PRIMARY KEY, '
        'access_token TEXT, '
        'token_expiry TIMESTAMP, '
        'rapt_token TEXT, '
        'id_token TEXT)'.format(_ACCESS_TOKEN_TABLE))

    # Older versions of the access_tokens database may not have the id_token
    # column, so we will add it if we can't access it.
    try:
      self._Execute(
          'SELECT id_token FROM "{}" LIMIT 1'.format(_ACCESS_TOKEN_TABLE))
    except sqlite3.OperationalError:
      self._Execute('ALTER TABLE "{}" ADD COLUMN id_token TEXT'.format(
          _ACCESS_TOKEN_TABLE))

  def _Execute(self, *args):
    with self._cursor as cur:
      cur.Execute(*args)

  def Load(self, account_id):
    with self._cursor as cur:
      return cur.Execute(
          'SELECT access_token, token_expiry, rapt_token, id_token '
          'FROM "{}" WHERE account_id = ?'
          .format(_ACCESS_TOKEN_TABLE), (account_id,)).fetchone()

  def Store(self, account_id, access_token, token_expiry, rapt_token, id_token):
    try:
      self._Execute(
          'REPLACE INTO "{}" '
          '(account_id, access_token, token_expiry, rapt_token, id_token) '
          'VALUES (?,?,?,?,?)'
          .format(_ACCESS_TOKEN_TABLE),
          (account_id, access_token, token_expiry, rapt_token, id_token))
    except sqlite3.OperationalError as e:
      log.warning('Could not store access token in cache: {}'.format(str(e)))

  def Remove(self, account_id):
    try:
      self._Execute(
          'DELETE FROM "{}" WHERE account_id = ?'
          .format(_ACCESS_TOKEN_TABLE), (account_id,))
    except sqlite3.OperationalError as e:
      log.warning('Could not delete access token from cache: {}'.format(str(e)))


class AccessTokenStore(client.Storage):
  """Oauth2client adapted for access token cache.

  This class works with Oauth2client model where access token is part of
  credential serialization format and get captured as part of that.
  By extending client.Storage this class pretends to serialize credentials, but
  only serializes access token.

  When fetching the more recent credentials from the cache, this does not return
  token_response, as it is now out of date.
  """

  def __init__(self, access_token_cache, account_id, credentials):
    """Sets up token store for given acount.

    Args:
      access_token_cache: AccessTokenCache, cache for access tokens.
      account_id: str, account for which token is stored.
      credentials: oauth2client.client.OAuth2Credentials, they are auto-updated
        with cached access token.
    """
    super(AccessTokenStore, self).__init__(lock=None)
    self._access_token_cache = access_token_cache
    self._account_id = account_id
    self._credentials = credentials

  def locked_get(self):
    token_data = self._access_token_cache.Load(self._account_id)
    if token_data:
      access_token, token_expiry, rapt_token, id_token = token_data
      self._credentials.access_token = access_token
      self._credentials.token_expiry = token_expiry
      if rapt_token is not None:
        self._credentials.rapt_token = rapt_token
      self._credentials.id_tokenb64 = id_token
      self._credentials.token_response = None
    return self._credentials

  def locked_put(self, credentials):
    if getattr(self._credentials, 'token_response'):
      id_token = self._credentials.token_response.get('id_token', None)
    else:
      id_token = None

    self._access_token_cache.Store(
        self._account_id,
        self._credentials.access_token,
        self._credentials.token_expiry,
        getattr(self._credentials, 'rapt_token', None),
        id_token)

  def locked_delete(self):
    self._access_token_cache.Remove(self._account_id)


class AccessTokenStoreGoogleAuth(object):
  """google-auth adapted for access token cache.

  This class works with google-auth credentials and serializes its short lived
  tokens, including access token, token expiry, rapt token, id token into the
  access token cache.
  """

  def __init__(self, access_token_cache, account_id, credentials):
    """Sets up token store for given account.

    Args:
      access_token_cache: AccessTokenCache, cache for access tokens.
      account_id: str, account for which token is stored.
      credentials: google.auth.credentials.Credentials, credentials of account
        of account_id.
    """
    self._access_token_cache = access_token_cache
    self._account_id = account_id
    self._credentials = credentials

  def Get(self):
    """Gets credentials with short lived tokens from the internal cache.

    Retrieves the short lived tokens from the internal access token cache,
    populates the credentials with these tokens and returns the credentials.

    Returns:
       google.auth.credentials.Credentials
    """
    token_data = self._access_token_cache.Load(self._account_id)
    if token_data:
      access_token, token_expiry, rapt_token, id_token = token_data
      if UseSelfSignedJwt(self._credentials):
        # For self signed jwt flow we only use the loaded id_token. Access token
        # will be generated; rapt token is always None for service account.
        self._credentials.token = None
        self._credentials.expiry = None
        self._credentials._rapt_token = None  # pylint: disable=protected-access
      else:
        self._credentials.token = access_token
        self._credentials.expiry = token_expiry
        self._credentials._rapt_token = rapt_token  # pylint: disable=protected-access
      # The id_token in cache and in google-auth creds is encoded. However,
      # the id_token of oauth2client creds is decoded and it adds another field
      # 'id_tokenb64' to store the encoded copy. To keep google-auth creds
      # consistent with oauth2client, we add it.
      self._credentials._id_token = id_token  # pylint: disable=protected-access
      self._credentials.id_tokenb64 = id_token
    return self._credentials

  def Put(self):
    """Puts the short lived tokens of the credentials to the internal cache."""
    id_token = getattr(self._credentials, 'id_tokenb64', None) or getattr(
        self._credentials, '_id_token', None
    )
    expiry = getattr(self._credentials, 'expiry', None)
    rapt_token = getattr(self._credentials, 'rapt_token', None)
    access_token = getattr(self._credentials, 'token', None)
    if UseSelfSignedJwt(self._credentials):
      # For self signed jwt, we only write the new ID token value into the
      # cache. For access token, expiry and rapt token we still use the
      # existing values in the cache. We reserve the cache for two-step refresh
      # flow (with token endpoint) so when users switch from one-step self
      # signed jwt flow they can still use the two-step flow tokens.
      # We first clear the access_token/expiry/rapt_token values obtained from
      # self._credentials, then set these values to those from the access token
      # cache, so when we write these values back to the access token cache,
      # they don't change in the cache.
      access_token = None
      expiry = None
      rapt_token = None
      token_data = self._access_token_cache.Load(self._account_id)
      if token_data:
        access_token, expiry, rapt_token, _ = token_data
    self._access_token_cache.Store(
        self._account_id, access_token, expiry, rapt_token, id_token
    )

  def Delete(self):
    """Removes the tokens of the account from the internal cache."""
    self._access_token_cache.Remove(self._account_id)


def MaybeAttachAccessTokenCacheStore(credentials,
                                     access_token_file=None):
  """Attaches access token cache to given credentials if no store set.

  Note that credentials themselves will not be persisted only access token. Use
  this whenever access token caching is desired, yet credentials themselves
  should not be persisted.

  Args:
    credentials: oauth2client.client.OAuth2Credentials.
    access_token_file: str, optional path to use for access token storage.
  Returns:
    oauth2client.client.OAuth2Credentials, reloaded credentials.
  """
  if credentials.store is not None:
    return credentials
  account_id = getattr(credentials, 'service_account_email', None)
  if not account_id:
    account_id = hashlib.sha256(six.ensure_binary(
        credentials.refresh_token)).hexdigest()

  access_token_cache = AccessTokenCache(
      access_token_file or config.Paths().access_token_db_path)
  store = AccessTokenStore(access_token_cache, account_id, credentials)
  credentials.set_store(store)
  # Return from the store, which will reload credentials with access token info.
  return store.get()


def MaybeAttachAccessTokenCacheStoreGoogleAuth(credentials,
                                               access_token_file=None):
  """Attaches access token cache to given credentials if no store set.

  Note that credentials themselves will not be persisted only access token. Use
  this whenever access token caching is desired, yet credentials themselves
  should not be persisted.

  For external account and external account authorized user non-impersonated
  credentials, the provided credentials should have been instantiated with
  the client_id and client_secret in order to retrieve the account ID from the
  3PI token instrospection endpoint.

  Args:
    credentials: google.auth.credentials.Credentials.
    access_token_file: str, optional path to use for access token storage.

  Returns:
    google.auth.credentials.Credentials, reloaded credentials.
  """
  account_id = getattr(credentials, 'service_account_email', None)
  # External account credentials without service account impersonation.
  # Use token introspection to get the account ID.
  if not account_id and (
      isinstance(credentials, google_auth_external_account.Credentials) or
      isinstance(credentials,
                 google_auth_external_account_authorized_user.Credentials)):
    account_id = c_introspect.GetExternalAccountId(credentials)
  elif not account_id:
    account_id = hashlib.sha256(six.ensure_binary(
        credentials.refresh_token)).hexdigest()

  access_token_cache = AccessTokenCache(access_token_file or
                                        config.Paths().access_token_db_path)
  store = AccessTokenStoreGoogleAuth(access_token_cache, account_id,
                                     credentials)
  credentials = store.Get()

  # google-auth credentials do not support auto caching access token on
  # credentials refresh. This logic needs to be implemented in gcloud.
  orig_refresh = credentials.refresh

  def _WrappedRefresh(request):
    orig_refresh(request)
    credentials.id_tokenb64 = getattr(credentials, '_id_token', None)
    # credentials are part of store. Calling Put() on store caches the
    # short lived tokens of the credentials.
    store.Put()

  credentials.refresh = _WrappedRefresh
  return credentials


class CredentialStoreWithCache(CredentialStore):
  """Implements CredentialStore for caching credentials information.

  Static credentials information, such as client ID and service account email,
  are stored in credentials.db. The short lived credentials tokens, such as
  access token, are cached in access_tokens.db.
  """

  def __init__(self, credential_store, access_token_cache):
    """Sets up credentials store for caching credentials.

    Args:
      credential_store: SqliteCredentialStore, for caching static credentials
        information, such as client ID, service account email, etc.
      access_token_cache: AccessTokenCache, for caching short lived credentials
        tokens, such as access token.
    """
    self._credential_store = credential_store
    self._access_token_cache = access_token_cache

  def _WrapCredentialsRefreshWithAutoCaching(self, credentials, store):
    """Wraps the refresh method of credentials with auto caching logic.

    For auto caching short lived tokens of google-auth credentials, such as
    access token, on credentials refresh.

    Args:
      credentials: google.auth.credentials.Credentials, the credentials updated
        by this method.
      store: AccessTokenStoreGoogleAuth, the store that caches the tokens of the
        input credentials.

    Returns:
      google.auth.credentials.Credentials, the updated credentials.
    """
    orig_refresh = credentials.refresh

    def _WrappedRefresh(request):
      orig_refresh(request)
      # credentials are part of store. Calling Put() on store caches the
      # short lived tokens of the credentials.
      store.Put()

    credentials.refresh = _WrappedRefresh
    return credentials

  def GetAccounts(self):
    """Returns all the accounts stored in the cache."""
    return self._credential_store.GetAccounts()

  def Load(self, account_id, use_google_auth=True):
    """Loads the credentials of account_id from the cache.

    Args:
      account_id: string, ID of the account to load.
      use_google_auth: bool, True to load google-auth credentials if the type of
        the credentials is supported by the cache. False to load oauth2client
        credentials.

    Returns:
      1. None, if credentials are not found in the cache.
      2. google.auth.credentials.Credentials, if use_google_auth is true.
      3. client.OAuth2Credentials.
    """
    # Loads static credentials information from self._credential_store.
    credentials = self._credential_store.Load(account_id, use_google_auth)
    if credentials is None:
      return None

    # Loads short lived tokens from self._access_token_cache.
    if IsOauth2ClientCredentials(credentials):
      store = AccessTokenStore(self._access_token_cache, account_id,
                               credentials)
      credentials.set_store(store)
      return store.get()
    else:
      store = AccessTokenStoreGoogleAuth(self._access_token_cache, account_id,
                                         credentials)
      credentials = store.Get()

      # google-auth credentials do not support auto caching access token on
      # credentials refresh. This logic needs to be implemented in gcloud.
      return self._WrapCredentialsRefreshWithAutoCaching(credentials, store)

  def Store(self, account_id, credentials):
    """Stores credentials into the cache with account of account_id.

    Args:
      account_id: string, the account that will be associated with credentials
        in the cache.
      credentials: google.auth.credentials.Credentials or
        client.OAuth2Credentials, the credentials to be stored.
    """
    # Stores short lived tokens to self._access_token_cache.
    if IsOauth2ClientCredentials(credentials):
      store = AccessTokenStore(self._access_token_cache, account_id,
                               credentials)
      credentials.set_store(store)
      store.put(credentials)
    else:
      store = AccessTokenStoreGoogleAuth(self._access_token_cache, account_id,
                                         credentials)
      store.Put()

    # Stores static credentials information to self._credential_store.
    self._credential_store.Store(account_id, credentials)

  def Remove(self, account_id):
    """Removes credentials of account_id from the cache."""
    self._credential_store.Remove(account_id)
    self._access_token_cache.Remove(account_id)


def GetCredentialStore(store_file=None,
                       access_token_file=None,
                       with_access_token_cache=True):
  """Constructs credential store.

  Args:
    store_file: str, optional path to use for storage. If not specified
      config.Paths().credentials_path will be used.

    access_token_file: str, optional path to use for access token storage. Note
      that some implementations use store_file to also store access_tokens, in
      which case this argument is ignored.
    with_access_token_cache: bool, True to load a credential store with
      auto caching for access tokens. False to load a credential store without
      auto caching for access tokens.

  Returns:
    CredentialStore object.
  """
  if with_access_token_cache:
    return _GetSqliteStoreWithCache(store_file, access_token_file)
  else:
    return _GetSqliteStore(store_file)


class CredentialType(enum.Enum):
  """Enum of oauth2client credential types managed by gcloud."""

  UNKNOWN = (0, UNKNOWN_CREDS_NAME, False, False)
  USER_ACCOUNT = (1, USER_ACCOUNT_CREDS_NAME, True, True)
  SERVICE_ACCOUNT = (2, SERVICE_ACCOUNT_CREDS_NAME, True, False)
  P12_SERVICE_ACCOUNT = (3, P12_SERVICE_ACCOUNT_CREDS_NAME, True, False)
  DEVSHELL = (4, DEVSHELL_CREDS_NAME, False, True)
  GCE = (5, GCE_CREDS_NAME, False, False)

  def __init__(self, type_id, key, is_serializable, is_user):
    self.type_id = type_id
    self.key = key
    self.is_serializable = is_serializable
    # True if this corresponds to a "user" or 3LO credential as opposed to a
    # service account of some kind.
    self.is_user = is_user

  @staticmethod
  def FromTypeKey(key):
    for cred_type in CredentialType:
      if cred_type.key == key:
        return cred_type
    return CredentialType.UNKNOWN

  @staticmethod
  def FromCredentials(creds):
    if isinstance(creds, oauth2client_gce.AppAssertionCredentials):
      return CredentialType.GCE
    if isinstance(creds, service_account.ServiceAccountCredentials):
      if getattr(creds, '_private_key_pkcs12', None) is not None:
        return CredentialType.P12_SERVICE_ACCOUNT
      return CredentialType.SERVICE_ACCOUNT
    if getattr(creds, 'refresh_token', None) is not None:
      return CredentialType.USER_ACCOUNT
    return CredentialType.UNKNOWN


class CredentialTypeGoogleAuth(enum.Enum):
  """Enum of google-auth credential types managed by gcloud."""

  UNKNOWN = (0, UNKNOWN_CREDS_NAME, False, False)
  USER_ACCOUNT = (1, USER_ACCOUNT_CREDS_NAME, True, True)
  SERVICE_ACCOUNT = (2, SERVICE_ACCOUNT_CREDS_NAME, True, False)
  P12_SERVICE_ACCOUNT = (3, P12_SERVICE_ACCOUNT_CREDS_NAME, False, False)
  DEVSHELL = (4, DEVSHELL_CREDS_NAME, True, True)
  GCE = (5, GCE_CREDS_NAME, True, False)
  IMPERSONATED_ACCOUNT = (6, IMPERSONATED_ACCOUNT_CREDS_NAME, True, False)
  # Workload identity pool credentials (impersonated and non-impersonated) or
  # impersonated workforce pool credentials.
  # These behave similarly to service accounts.
  EXTERNAL_ACCOUNT = (7, EXTERNAL_ACCOUNT_CREDS_NAME, True, False)
  # Workforce pool credentials. These are non-Google end user credentials.
  # No service account impersonation is used with these credentials, otherwise
  # they are considered EXTERNAL_ACCOUNT credentials.
  EXTERNAL_ACCOUNT_USER = (8, EXTERNAL_ACCOUNT_USER_CREDS_NAME, True, True)
  # Workforce pool credentials obtained via headful sign-in. These are
  # non-Google end user credentials. No service account impersonation is used
  # with these credentials.
  EXTERNAL_ACCOUNT_AUTHORIZED_USER = (
      9, EXTERNAL_ACCOUNT_AUTHORIZED_USER_CREDS_NAME, True, True)

  def __init__(self, type_id, key, is_serializable, is_user):
    """Builds a credentials type instance given the credentials information.

    Args:
      type_id: string, ID for the credentials type, based on the enum constant
        value of the type.
      key: string, key of the credentials type, based on the enum constant value
        of the type.
      is_serializable: bool, whether the type of the credentials is
        serializable, based on the enum constant value of the type.
      is_user: bool, True if the credentials are of user account. False
        otherwise.

    Returns:
      CredentialTypeGoogleAuth, an instance of CredentialTypeGoogleAuth which
        is a gcloud internal representation of type of the google-auth
        credentials.
    """
    self.type_id = type_id
    self.key = key
    self.is_serializable = is_serializable
    # True if this corresponds to a "user" or 3LO credential as opposed to a
    # service account of some kind.
    self.is_user = is_user

  @staticmethod
  def FromTypeKey(key):
    """Returns the credentials type based on the input key."""
    for cred_type in CredentialTypeGoogleAuth:
      if cred_type.key == key:
        return cred_type
    return CredentialTypeGoogleAuth.UNKNOWN

  @staticmethod
  def FromCredentials(creds):
    """Returns the credentials type based on the input credentials."""
    if isinstance(creds, google_auth_compute_engine.Credentials):
      return CredentialTypeGoogleAuth.GCE
    if isinstance(creds, google_auth_impersonated.Credentials):
      return CredentialTypeGoogleAuth.IMPERSONATED_ACCOUNT
    if (isinstance(creds, google_auth_external_account.Credentials) and
        not creds.is_user):
      return CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT
    if (isinstance(creds, google_auth_external_account.Credentials) and
        creds.is_user):
      return CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_USER
    if (isinstance(creds,
                   google_auth_external_account_authorized_user.Credentials)):
      return CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_AUTHORIZED_USER
    # Import only when necessary to decrease the startup time. Move it to
    # global once google-auth is ready to replace oauth2client.
    # pylint: disable=g-import-not-at-top
    from google.oauth2 import service_account as google_auth_service_account
    from googlecloudsdk.core.credentials import p12_service_account as google_auth_p12_service_account
    # pylint: enable=g-import-not-at-top
    if isinstance(creds, google_auth_p12_service_account.Credentials):
      return CredentialTypeGoogleAuth.P12_SERVICE_ACCOUNT
    if isinstance(creds, google_auth_service_account.Credentials):
      return CredentialTypeGoogleAuth.SERVICE_ACCOUNT
    if getattr(creds, 'refresh_token', None) is not None:
      return CredentialTypeGoogleAuth.USER_ACCOUNT
    return CredentialTypeGoogleAuth.UNKNOWN


def ToJson(credentials):
  """Given Oauth2client credentials return library independent json for it."""
  creds_type = CredentialType.FromCredentials(credentials)
  if creds_type == CredentialType.USER_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'refresh_token': credentials.refresh_token
    }
    # These fields are optionally serialized as they are not required for
    # credentials to be usable, these are used by Oauth2client.
    for field in ('id_token', 'invalid', 'revoke_uri', 'scopes',
                  'token_response', 'token_uri', 'user_agent', 'rapt_token'):
      value = getattr(credentials, field, None)
      if value:
        # Sets are not json serializable as is, so encode as a list.
        if isinstance(value, set):
          value = list(value)
        creds_dict[field] = value

  elif creds_type == CredentialType.SERVICE_ACCOUNT:
    creds_dict = credentials.serialization_data
  elif creds_type == CredentialType.P12_SERVICE_ACCOUNT:
    # pylint: disable=protected-access
    creds_dict = {
        'client_email': credentials._service_account_email,
        'type': creds_type.key,
        # The base64 only deals with bytes. The encoded value is bytes but is
        # known to be a safe ascii string. To serialize it, convert it to a
        # text object.
        'private_key': (base64.b64encode(credentials._private_key_pkcs12)
                        .decode('ascii')),
        'password': credentials._private_key_password
    }
  else:
    raise UnknownCredentialsType(creds_type)
  return json.dumps(creds_dict, sort_keys=True,
                    indent=2, separators=(',', ': '))


def ToJsonGoogleAuth(credentials):
  """Given google-auth credentials, return library independent json for it."""
  creds_type = CredentialTypeGoogleAuth.FromCredentials(credentials)
  if creds_type == CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_email': credentials.service_account_email,
        'private_key_id': credentials.private_key_id,
        'private_key': credentials.private_key,
        'client_id': credentials.client_id,
        # '_token_uri' is not exposed in a public property in the service
        # credentials implementation which does not currently support
        # serialization, so pylint: disable=protected-access
        'token_uri': credentials._token_uri,  # pylint: disable=protected-access
        'project_id': credentials.project_id,
    }
  elif (creds_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT or
        creds_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_USER):
    # The credentials should already have the JSON representation set on info
    # property.
    creds_dict = credentials.info
    # Pluggable auth doesn't overwrite the "info" method.
    # We manually inject tokeninfo_username for later retrieve and injection.
    # TODO(b/258323440)
    if credentials.is_workforce_pool and hasattr(credentials, 'interactive'):
      creds_dict['external_account_id'] = credentials.external_account_id
  elif creds_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_AUTHORIZED_USER:
    creds_dict = {
        'type': creds_type.key,
        'audience': credentials.audience,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'refresh_token': credentials.refresh_token,
        'token_url': credentials.token_url,
        'token_info_url': credentials.token_info_url,
    }
  elif creds_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'refresh_token': credentials.refresh_token,
        'revoke_uri': _REVOKE_URI,
        'scopes': credentials._scopes,  # pylint: disable=protected-access
        'token_uri': credentials.token_uri,
    }
  elif creds_type == CredentialTypeGoogleAuth.P12_SERVICE_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_email': credentials.service_account_email,
        # The base64 only deals with bytes. The encoded value is bytes but is
        # known to be a safe ascii string. To serialize it, convert it to a
        # text object.
        'private_key':
            (base64.b64encode(credentials.private_key_pkcs12).decode('ascii')),
        'password': credentials.private_key_password
    }
  elif creds_type == CredentialTypeGoogleAuth.GCE:
    creds_dict = {
        'type': creds_type.key,
        'service_account_email': credentials.service_account_email,
    }
  else:
    raise UnknownCredentialsType(
        'Google auth does not support serialization of {} credentials.'.format(
            creds_type.key))

  # Save universe_domain.
  creds_dict['universe_domain'] = credentials.universe_domain

  return json.dumps(
      creds_dict, sort_keys=True, indent=2, separators=(',', ': '))


def SerializeCredsGoogleAuth(credentials):
  """Given google-auth credentials, return serialized json string.

  This method is added because google-auth credentials are not serializable
  natively.

  Args:
    credentials: google-auth credential object.

  Returns:
    Json string representation of the credential.
  """
  creds_dict = ToDictGoogleAuth(credentials)
  return json.dumps(
      creds_dict, sort_keys=True, indent=2, separators=(',', ': '))


def ToDictGoogleAuth(credentials):
  """Given google-auth credentials, recursively return dict representation.

  This method is added because google-auth credentials are not serializable
  natively.

  Args:
    credentials: google-auth credential object.

  Returns:
    Dict representation of the credential.

  Raises:
    UnknownCredentialsType: An error for when we fail to determine the type
    of the credentials.
  """
  creds_type = CredentialTypeGoogleAuth.FromCredentials(credentials)

  if not creds_type.is_serializable:
    raise UnknownCredentialsType(
        'Google auth does not support serialization of {} credentials.'.format(
            creds_type.key))

  creds_dict = {'type': creds_type.key}
  # Serializing all attributes found on the credential object. Since
  # credentials generated in different scenarios contain different attributes,
  # no predefined attribute lists are used. Do not include `signer` as it is a
  # repeated field. Do not include class attributes that start with `__`.
  # Do not include `_abc_negative_cache_version` as this attribute is
  # irrelevant to the credentials.
  filtered_list = [attr for attr in dir(credentials)
                   if not attr.startswith('__') and
                   attr not in ['signer', '_abc_negative_cache_version']]
  # Include protected attributes that do not have a corresponding non-protected
  # attribute.
  attr_list = [attr for attr in filtered_list
               if not attr.startswith('_') or attr[1:] not in filtered_list]
  attr_list = sorted(attr_list)
  for attr in attr_list:
    if hasattr(credentials, attr):
      val = getattr(credentials, attr)
      val_type = type(val)
      if val_type == datetime.datetime:
        val = val.strftime('%m-%d-%Y %H:%M:%S')
      # Nested credential object
      elif issubclass(val_type, google_auth_creds.Credentials):
        try:
          val = ToDictGoogleAuth(val)
        except UnknownCredentialsType:
          continue
      # Allow only primitive types and list/dict/tuple for json dump input.
      elif (val is not None and not isinstance(val, six.string_types) and
            val_type not in (int, float, bool, str, list, dict, tuple)):
        continue
      creds_dict[attr] = val

  return creds_dict


def FromJson(json_value):
  """Returns Oauth2client credentials from library independent json format."""
  json_key = json.loads(json_value)
  cred_type = CredentialType.FromTypeKey(json_key['type'])
  json_key['token_uri'] = GetEffectiveTokenUri(json_key)
  if cred_type == CredentialType.SERVICE_ACCOUNT:
    cred = service_account.ServiceAccountCredentials.from_json_keyfile_dict(
        json_key, scopes=config.CLOUDSDK_SCOPES)
    cred.user_agent = cred._user_agent = config.CLOUDSDK_USER_AGENT
  elif cred_type == CredentialType.USER_ACCOUNT:
    cred = client.OAuth2Credentials(
        access_token=None,
        client_id=json_key['client_id'],
        client_secret=json_key['client_secret'],
        refresh_token=json_key['refresh_token'],
        token_expiry=None,
        token_uri=json_key.get('token_uri'),
        user_agent=json_key.get('user_agent'),
        revoke_uri=json_key.get('revoke_uri'),
        id_token=json_key.get('id_token'),
        token_response=json_key.get('token_response'),
        scopes=json_key.get('scopes'),
        token_info_uri=json_key.get('token_info_uri'),
        rapt_token=json_key.get('rapt_token'),
    )
  elif cred_type == CredentialType.P12_SERVICE_ACCOUNT:
    # pylint: disable=protected-access
    cred = service_account.ServiceAccountCredentials._from_p12_keyfile_contents(
        service_account_email=json_key['client_email'],
        private_key_pkcs12=base64.b64decode(json_key['private_key']),
        private_key_password=json_key['password'],
        token_uri=json_key['token_uri'],
        scopes=config.CLOUDSDK_SCOPES)
    cred.user_agent = cred._user_agent = config.CLOUDSDK_USER_AGENT
  else:
    raise UnknownCredentialsType(json_key['type'])
  return cred


def FromJsonGoogleAuth(json_value):
  """Returns google-auth credentials from library independent json format.

  The type of the credentials could be service account, external account
  (workload identity pool or workforce pool), external account authorized user
  (workforce), user account, p12 service account, or compute engine.

  Args:
    json_value: string, A string of the JSON representation of the credentials.

  Returns:
    google.auth.credentials.Credentials if the credentials type is supported
    by this method.

  Raises:
    UnknownCredentialsType: when the type of the credentials is not service
      account, user account or external account.
    InvalidCredentialsError: when the provided credentials are malformed or
      unsupported external account credentials.
  """
  json_key = json.loads(json_value)
  cred_type = CredentialTypeGoogleAuth.FromTypeKey(json_key['type'])
  if cred_type == CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    json_key['token_uri'] = GetEffectiveTokenUri(json_key)
    # Import only when necessary to decrease the startup time. Move it to
    # global once google-auth is ready to replace oauth2client.
    # pylint: disable=g-import-not-at-top
    from google.oauth2 import service_account as google_auth_service_account
    # pylint: enable=g-import-not-at-top
    service_account_credentials = (
        google_auth_service_account.Credentials.from_service_account_info)
    cred = service_account_credentials(json_key, scopes=config.CLOUDSDK_SCOPES)
    # The following fields are not members of the google-auth credentials which
    # are not designed to support persistent caching. These fields will be used
    # by gcloud to build google-auth credentials from cache data.
    cred.private_key = json_key.get('private_key')
    cred.private_key_id = json_key.get('private_key_id')
    cred.client_id = json_key.get('client_id')
    # Enable self signed jwt if applicable for the cred created from cred store.
    EnableSelfSignedJwtIfApplicable(cred)
    return cred
  if cred_type == CredentialTypeGoogleAuth.P12_SERVICE_ACCOUNT:
    json_key['token_uri'] = GetEffectiveTokenUri(json_key)
    from googlecloudsdk.core.credentials import p12_service_account  # pylint: disable=g-import-not-at-top
    cred = p12_service_account.CreateP12ServiceAccount(
        base64.b64decode(json_key['private_key']),
        json_key['password'],
        service_account_email=json_key['client_email'],
        token_uri=json_key['token_uri'],
        scopes=config.CLOUDSDK_SCOPES)
    return cred
  if cred_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT:
    # token_uri is not applicable to external account credentials.
    # A different endpoint is used for token exchange (GCP STS).
    # These credentials can also be user credentials EXTERNAL_ACCOUNT_USER.
    # Both credentials use "exernal_account" as "type" in the JSON file.

    # Use client authentication when no impersonation is used. This is needed
    # in order to call 3PI token introspection which requires the provided
    # token be authenticated with gcloud client auth.
    if 'service_account_impersonation_url' not in json_key:
      json_key['client_id'] = config.CLOUDSDK_CLIENT_ID
      json_key['client_secret'] = config.CLOUDSDK_CLIENT_NOTSOSECRET

    try:
      if json_key.get('subject_token_type'
                     ) == 'urn:ietf:params:aws:token-type:aws4_request':
        # Check if configuration corresponds to an AWS credentials.
        from google.auth import aws  # pylint: disable=g-import-not-at-top
        cred = aws.Credentials.from_info(
            json_key, scopes=config.CLOUDSDK_SCOPES)
      elif (json_key.get('credential_source') is not None and
            json_key.get('credential_source').get('executable') is not None):
        from google.auth import pluggable  # pylint: disable=g-import-not-at-top
        executable = json_key.get('credential_source').get('executable')
        cred = pluggable.Credentials.from_info(
            json_key, scopes=config.CLOUDSDK_SCOPES)
        if cred.is_workforce_pool and executable.get(
            'interactive_timeout_millis'):
          cred.interactive = True
          # Currently we manually inject the external_account_id.
          # TODO(b/258323440). Once we have the change done in SDK, we remove
          # the current injection.
          setattr(cred, '_tokeninfo_username',
                  json_key.get('external_account_id') or '')
      else:
        from google.auth import identity_pool  # pylint: disable=g-import-not-at-top
        cred = identity_pool.Credentials.from_info(
            json_key, scopes=config.CLOUDSDK_SCOPES)
    except (ValueError, TypeError, google_auth_exceptions.RefreshError):
      raise InvalidCredentialsError(
          'The provided external account credentials are invalid or '
          'unsupported')
    return WrapGoogleAuthExternalAccountRefresh(cred)

  if cred_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_AUTHORIZED_USER:
    # token_uri is applicable to external account authorized user credentials
    # but is not configurable via auth properties. The config remains the
    # source of truth.

    # Client authentication is needed in order to call 3PI token introspection
    # which requires the provided token be authenticated with gcloud client
    # auth.
    json_key['client_id'] = config.CLOUDSDK_CLIENT_ID
    json_key['client_secret'] = config.CLOUDSDK_CLIENT_NOTSOSECRET

    json_key['scopes'] = config.CLOUDSDK_EXTERNAL_ACCOUNT_SCOPES
    try:
      # Attempt to initialize external account authorized user credentials.
      cred = google_auth_external_account_authorized_user.Credentials.from_info(
          json_key)
    except (ValueError, TypeError, google_auth_exceptions.RefreshError):
      raise InvalidCredentialsError(
          'The provided external account authorized user credentials are '
          'invalid or unsupported')
    return WrapGoogleAuthExternalAccountRefresh(cred)

  if cred_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    json_key['token_uri'] = GetEffectiveTokenUri(json_key)
    # Import only when necessary to decrease the startup time. Move it to
    # global once google-auth is ready to replace oauth2client.
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
    # pylint: enable=g-import-not-at-top

    cred = c_google_auth.Credentials.from_authorized_user_info(
        json_key, scopes=json_key.get('scopes'))
    # token_uri is hard-coded in google-auth library, replace it.
    cred._token_uri = json_key['token_uri']  # pylint: disable=protected-access
    return cred

  if cred_type == CredentialTypeGoogleAuth.GCE:
    cred = google_auth_compute_engine.Credentials(
        service_account_email=json_key['service_account_email'],
    )
    cred._universe_domain = json_key.get(  # pylint: disable=protected-access
        'universe_domain', properties.VALUES.core.universe_domain.default
    )
    # Set _universe_domain_cached to True to re-use the _universe_domain value
    # instead of fetching it from metadata server.
    cred._universe_domain_cached = True  # pylint: disable=protected-access
    return cred

  raise UnknownCredentialsType(
      'Google auth does not support deserialization of {} credentials.'.format(
          json_key['type']))


def WrapGoogleAuthExternalAccountRefresh(cred):
  """Returns a wrapped External Account credentials.

  We wrap the refresh method to make sure that any errors raised can be caught
  in a consistent way by downstream consumers.

  Args:
    cred: google.auth.credentials.Credentials

  Returns:
    google.auth.credentials.Credentials
  """

  orig_refresh = cred.refresh

  def _WrappedRefresh(request):
    try:
      orig_refresh(request)
    except (ValueError, TypeError, google_auth_exceptions.RefreshError) as e:
      raise c_exceptions.TokenRefreshError(e)

  cred.refresh = _WrappedRefresh
  return cred


def _GetSqliteStoreWithCache(sqlite_credential_file=None,
                             sqlite_access_token_file=None):
  """Get a sqlite-based Credential Store."""

  credential_store = _GetSqliteStore(sqlite_credential_file)

  sqlite_access_token_file = (sqlite_access_token_file or
                              config.Paths().access_token_db_path)
  files.PrivatizeFile(sqlite_access_token_file)
  access_token_cache = AccessTokenCache(sqlite_access_token_file)
  return CredentialStoreWithCache(credential_store, access_token_cache)


def _GetSqliteStore(sqlite_credential_file=None):
  """Get a sqlite-based Credential Store with using the access token cache."""
  sqlite_credential_file = (sqlite_credential_file or
                            config.Paths().credentials_db_path)
  files.PrivatizeFile(sqlite_credential_file)
  credential_store = SqliteCredentialStore(sqlite_credential_file)
  return credential_store


def _QuotaProjectIsCurrentProject(quota_project):
  return quota_project in (
      properties.VALUES.billing.CURRENT_PROJECT,
      properties.VALUES.billing.CURRENT_PROJECT_WITH_FALLBACK)


def GetQuotaProject(credentials, force_resource_quota=False):
  """Gets the value to use for the X-Goog-User-Project header.

  Args:
    credentials: The credentials that are going to be used for requests.
    force_resource_quota: bool, If true, resource project quota will be used
      even if gcloud is set to use legacy mode for quota. This should be set
      when calling newer APIs that would not work without resource quota.

  Returns:
    str, The project id to send in the header or None to not populate the
    header.
  """
  if credentials is None:
    return None

  quota_project = properties.VALUES.billing.quota_project.Get()
  if _QuotaProjectIsCurrentProject(quota_project):
    if IsUserAccountCredentials(credentials):
      return properties.VALUES.core.project.Get()
    else:
      # for service account, don't return if flag or property are not set
      return None
  elif quota_project == properties.VALUES.billing.LEGACY:
    if force_resource_quota:
      return properties.VALUES.core.project.Get()
    return None
  return quota_project


class ADC(object):
  """Application default credential object."""

  def __init__(self,
               credentials,
               impersonated_service_account=None,
               delegates=None):
    self._credentials = credentials
    self._impersonated_service_account = impersonated_service_account
    self._delegates = delegates

  @property
  def is_user(self):
    return (IsUserAccountCredentials(self._credentials) and
            self._impersonated_service_account is None)

  @property
  def adc(self):
    """Json representation of the credentials for ADC."""
    return _ConvertCredentialsToADC(self._credentials,
                                    self._impersonated_service_account,
                                    self._delegates)

  def DumpADCToFile(self, file_path=None):
    """Dumps the credentials to the ADC json file."""
    file_path = file_path or config.ADCFilePath()
    return _DumpADCJsonToFile(self.adc, file_path)

  def DumpExtendedADCToFile(self, file_path=None, quota_project=None):
    """Dumps the credentials and the quota project to the ADC json file."""
    if not self.is_user:
      raise CredentialFileSaveError(
          'The credential is not a user credential, so we cannot insert a '
          'quota project to application default credential.')
    file_path = file_path or config.ADCFilePath()
    if not quota_project:
      quota_project = GetQuotaProject(
          self._credentials, force_resource_quota=True)
    extended_adc = self._ExtendADCWithQuotaProject(quota_project)
    return _DumpADCJsonToFile(extended_adc, file_path)

  def _ExtendADCWithQuotaProject(self, quota_project):
    """Add quota_project_id field to ADC json."""
    extended_adc = copy.deepcopy(self.adc)
    if quota_project:
      extended_adc[ADC_QUOTA_PROJECT_FIELD_NAME] = quota_project
    else:
      log.warning(
          'Cannot find a project to insert into application default '
          'credentials (ADC) as a quota project.\n'
          'Run $gcloud auth application-default set-quota-project to insert a '
          'quota project to ADC.')
    return extended_adc


def _DumpADCJsonToFile(adc, file_path):
  """Dumps ADC json object to file."""
  try:
    contents = json.dumps(adc, sort_keys=True, indent=2, separators=(',', ': '))
    files.WriteFileContents(file_path, contents, private=True)
  except files.Error as e:
    log.debug(e, exc_info=True)
    raise CredentialFileSaveError(
        'Error saving Application Default Credentials: ' + six.text_type(e))
  return os.path.abspath(file_path)


def _ConvertOauth2ClientCredentialsToADC(credentials):
  """Converts an oauth2client credentials to application default credentials."""
  creds_type = CredentialType.FromCredentials(credentials)
  if creds_type not in (CredentialType.USER_ACCOUNT,
                        CredentialType.SERVICE_ACCOUNT):
    raise ADCError('Cannot convert credentials of type {} to application '
                   'default credentials.'.format(type(credentials)))
  if creds_type == CredentialType.USER_ACCOUNT:
    credentials = client.GoogleCredentials(
        credentials.access_token, credentials.client_id,
        credentials.client_secret, credentials.refresh_token,
        credentials.token_expiry, credentials.token_uri, credentials.user_agent,
        credentials.revoke_uri)
  return credentials.serialization_data


IMPERSONATION_TOKEN_URL = 'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken'


def _ConvertCredentialsToADC(credentials, impersonated_service_account,
                             delegates):
  """Convert credentials with impersonation to a json dictionary."""
  if IsOauth2ClientCredentials(credentials):
    creds_dict = _ConvertOauth2ClientCredentialsToADC(credentials)
  else:
    creds_dict = _ConvertGoogleAuthCredentialsToADC(credentials)

  if not impersonated_service_account:
    return creds_dict
  impersonated_creds_dict = {
      'source_credentials':
          creds_dict,
      'service_account_impersonation_url':
          IMPERSONATION_TOKEN_URL.format(impersonated_service_account),
      'delegates':
          delegates or [],
      'type':
          'impersonated_service_account'
  }
  return impersonated_creds_dict


def _ConvertGoogleAuthCredentialsToADC(credentials):
  """Converts a google-auth credentials to application default credentials."""
  creds_type = CredentialTypeGoogleAuth.FromCredentials(credentials)
  if creds_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    adc = credentials.to_json(strip=('token', 'token_uri', 'scopes', 'expiry'))
    adc = json.loads(adc)
    adc['type'] = creds_type.key
    return adc
  if creds_type == CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    return {
        'type': creds_type.key,
        'client_email': credentials.service_account_email,
        'private_key_id': credentials.private_key_id,
        'private_key': credentials.private_key,
        'client_id': credentials.client_id,
        'token_uri': credentials._token_uri,  # pylint: disable=protected-access
        'universe_domain': credentials.universe_domain,
    }
  if (creds_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT or
      creds_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_USER):
    # These credentials will be used by the client libraries. We do not need
    # to keep the gcloud client ID and secret in the generated credentials as
    # account ID determination is not required there.
    adc_json = credentials.info
    adc_json.pop('client_id', None)
    adc_json.pop('client_secret', None)
    return adc_json
  if creds_type == CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_AUTHORIZED_USER:
    adc_json = credentials.to_json(strip=('token', 'expiry', 'scopes'))
    adc_json = json.loads(adc_json)
    if getattr(credentials, 'universe_domain', None) is not None:
      adc_json['universe_domain'] = credentials.universe_domain
    return adc_json

  raise ADCError('Cannot convert credentials of type {} to application '
                 'default credentials.'.format(type(credentials)))


GOOGLE_AUTH_DEFAULT = None
VERBOSITY_MUTED = log.VALID_VERBOSITY_STRINGS['none']


def GetGoogleAuthDefault():
  """Get the google.auth._default module.

  All messages from logging and warnings are muted because they are for
  ADC consumers (client libraries). The message are irrelevant and confusing to
  gcloud auth application-default users. gcloud auth application-default
  are the ADC producer.

  Returns:
    The google.auth._default module with logging/warnings muted.
  """
  global GOOGLE_AUTH_DEFAULT
  if GOOGLE_AUTH_DEFAULT:
    return GOOGLE_AUTH_DEFAULT
  # pylint: disable=g-import-not-at-top
  from google.auth import _default
  import warnings
  # pylint: enable=g-import-not-at-top
  warnings.filterwarnings(
      'ignore', category=Warning, module='google.auth._default')
  _default._LOGGER.setLevel(VERBOSITY_MUTED)  # pylint: disable=protected-access
  GOOGLE_AUTH_DEFAULT = _default
  return GetGoogleAuthDefault()
