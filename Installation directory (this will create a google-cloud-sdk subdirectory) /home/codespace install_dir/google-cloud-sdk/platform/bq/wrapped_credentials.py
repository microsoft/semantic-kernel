#!/usr/bin/env python
"""Classes and functions to allow google.auth credentials to be used within oauth2client.

In particular, the External Account credentials don't have an equivalent in
oauth2client, so we create helper methods to allow variants of this particular
class to be used in oauth2client workflows.
"""
import copy
import datetime
import io
import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from google.auth import aws
from google.auth import external_account
from google.auth import external_account_authorized_user
from google.auth import identity_pool
from google.auth import pluggable
from google.auth.transport import requests
import oauth2client_4_0

import bq_utils


class WrappedCredentials(oauth2client_4_0.client.OAuth2Credentials):
  """A utility class to use Google Auth credentials in place of oauth2client credentials.
  """
  NON_SERIALIZED_MEMBERS = frozenset(
      list(oauth2client_4_0.client.OAuth2Credentials.NON_SERIALIZED_MEMBERS) +
      ['_base'])

  def __init__(
      self,
      base_creds: (
          'external_account.Credentials | '
          'external_account_authorized_user.Credentials'
      ),
  ) -> None:
    """Initializes oauth2client credentials based on underlying Google Auth credentials.

    Args:
      base_creds: subclass of
        google.auth.external_account.Credentials or
        google.auth.external_account_authorized_user.Credentials
    """

    if not isinstance(
        base_creds, external_account.Credentials) and not isinstance(
            base_creds, external_account_authorized_user.Credentials):
      raise TypeError('Invalid Credentials')
    self._base = base_creds
    super().__init__(
        access_token=self._base.token,
        client_id=self._base._audience,
        client_secret=None,
        refresh_token=None,
        token_expiry=self._base.expiry,
        token_uri=None,
        user_agent=None,
    )

  def _do_refresh_request(self, http: 'requests.Request') -> None:
    self._base.refresh(requests.Request())
    if self.store is not None:
      self.store.locked_put(self)

  @property
  def access_token(self) -> str:
    return self._base.token

  @access_token.setter
  def access_token(self, value: str) -> None:
    self._base.token = value

  @property
  def token_expiry(self) -> datetime.datetime:
    return self._base.expiry

  @token_expiry.setter
  def token_expiry(self, value: datetime.datetime):
    self._base.expiry = value

  @property
  def scopes(self) -> List[str]:
    return self._base._scopes  # pylint: disable=protected-access

  @scopes.setter
  def scopes(self, value: List[str]) -> None:
    if value:
      self._base._scopes = value  # pylint: disable=protected-access

  def to_json(self) -> str:
    """Utility function that creates JSON representation of a Credentials object.

    Returns:
        string, a JSON representation of this instance, suitable to pass to
        from_json().
    """

    serialized_data = super(WrappedCredentials, self).to_json()
    deserialized_data = json.loads(serialized_data)
    deserialized_data['_base'] = copy.copy(self._base.info)
    deserialized_data['access_token'] = self._base.token
    deserialized_data['token_expiry'] = _parse_expiry(self.token_expiry)
    return json.dumps(deserialized_data)

  @classmethod
  def for_external_account(cls, filename: str) -> 'WrappedCredentials':
    creds = _get_external_account_credentials_from_file(filename)
    return cls(creds)

  @classmethod
  def for_external_account_authorized_user(
      cls, filename: str
  ) -> 'WrappedCredentials':
    creds = _get_external_account_authorized_user_credentials_from_file(
        filename)
    return cls(creds)

  @classmethod
  def from_json(cls, json_data: str) -> 'WrappedCredentials':
    """Instantiate a Credentials object from a JSON description of it.

    The JSON should have been produced by calling .to_json() on the object.

    Args:
        json_data: dict, A deserialized JSON object.

    Returns:
        An instance of a Credentials subclass.
    """

    data = json.loads(json_data)
    # Rebuild the credentials.
    base = data.get('_base')
    # Init base cred.
    base_creds = None
    if base.get('type') == 'external_account':
      base_creds = _get_external_account_credentials_from_info(base)
    elif base.get('type') == 'external_account_authorized_user':
      base_creds = _get_external_account_authorized_user_credentials_from_info(
          base)
    creds = cls(base_creds)
    # Inject token and expiry.
    creds.access_token = data.get('access_token')
    if (data.get('token_expiry') and
        not isinstance(data['token_expiry'], datetime.datetime)):
      try:
        data['token_expiry'] = datetime.datetime.strptime(
            data['token_expiry'], oauth2client_4_0.client.EXPIRY_FORMAT)
      except ValueError:
        data['token_expiry'] = None
    creds.token_expiry = data.get('token_expiry')

    return creds


def _get_external_account_credentials_from_info(
    info: Dict[str, Dict[str, object]]
) -> 'external_account.Credentials':
  """Create External Account Credentials using the mapping provided as json data.

  Finds a relevant subclass of external_account.Credentials and instantiates.

  Args:
      info: dict, A deserialized JSON object.

  Returns:
      An instance of a Credentials class
  """

  scopes = bq_utils.GetClientScopesFromFlags()
  if info.get(
      'subject_token_type') == 'urn:ietf:params:aws:token-type:aws4_request':
    # Configuration corresponds to an AWS credentials.
    return aws.Credentials.from_info(info, scopes=scopes)
  elif info.get('credential_source', {}).get('executable') is not None:
    # Configuration corresponds to pluggable credentials.
    return pluggable.Credentials.from_info(info, scopes=scopes)
  else:
    # Configuration corresponds to an identity pool credentials.
    return identity_pool.Credentials.from_info(info, scopes=scopes)


def _get_external_account_credentials_from_file(
    filename: str,
) -> 'external_account.Credentials':
  with io.open(filename, 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)
    return _get_external_account_credentials_from_info(data)


def _get_external_account_authorized_user_credentials_from_info(
    info: Dict[str, object]
) -> 'external_account_authorized_user.Credentials':
  """Create External Account Authorized User Credentials using the mapping provided as json data.

  Args:
      info: dict, A deserialized JSON object.

  Returns:
      An instance of a Credentials class
  """
  scopes = bq_utils.GetClientScopesFor3pi()
  info.update(scopes=scopes)
  return external_account_authorized_user.Credentials.from_info(info)


def _get_external_account_authorized_user_credentials_from_file(
    filename: str,
) -> 'external_account_authorized_user.Credentials':
  with io.open(filename, 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)
    return _get_external_account_authorized_user_credentials_from_info(data)


def _parse_expiry(expiry: Any) -> Optional[str]:
  if expiry and isinstance(expiry, datetime.datetime):
    return expiry.strftime(oauth2client_4_0.client.EXPIRY_FORMAT)
  else:
    return None
