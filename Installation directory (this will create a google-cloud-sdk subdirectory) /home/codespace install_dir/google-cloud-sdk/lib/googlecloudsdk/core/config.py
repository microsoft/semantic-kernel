# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Config for Google Cloud CLIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import logging
import os
import sqlite3
import time
from typing import Dict
import uuid

from google.auth import _cloud_sdk
from google.auth import environment_vars
import googlecloudsdk
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import pkg_resources
from googlecloudsdk.core.util import platforms
import six


class Error(exceptions.Error):
  """Exceptions for the cli module."""


# Environment variable for the directory containing Cloud SDK configuration.
CLOUDSDK_CONFIG = 'CLOUDSDK_CONFIG'

# Environment variable for overriding the Cloud SDK active named config
CLOUDSDK_ACTIVE_CONFIG_NAME = 'CLOUDSDK_ACTIVE_CONFIG_NAME'


class InstallationConfig(object):
  """Loads configuration constants from the core config file.

  Attributes:
    version: str, The version of the core component.
    revision: long, A revision number from a component snapshot.  This is a long
      int but formatted as an actual date in seconds (i.e 20151009132504). It is
      *NOT* seconds since the epoch.
    user_agent: str, The base string of the user agent to use when making API
      calls.
    documentation_url: str, The URL where we can redirect people when they need
      more information.
    release_notes_url: str, The URL where we host a nice looking version of our
      release notes.
    snapshot_url: str, The url for the component manager to look at for updates.
    disable_updater: bool, True to disable the component manager for this
      installation.  We do this for distributions through another type of
      package manager like apt-get.
    disable_usage_reporting: bool, True to disable the sending of usage data by
      default.
    snapshot_schema_version: int, The version of the snapshot schema this code
      understands.
    release_channel: str, The release channel for this Cloud SDK distribution.
    config_suffix: str, A string to add to the end of the configuration
      directory name so that different release channels can have separate
      config.
  """

  REVISION_FORMAT_STRING = '%Y%m%d%H%M%S'

  @staticmethod
  def Load():
    """Initializes the object with values from the config file.

    Returns:
      InstallationSpecificData: The loaded data.
    """
    data = json.loads(
        encoding.Decode(pkg_resources.GetResource(__name__, 'config.json'))
    )
    return InstallationConfig(**data)

  @staticmethod
  def FormatRevision(time_struct):
    """Formats a given time as a revision string for a component snapshot.

    Args:
      time_struct: time.struct_time, The time you want to format.

    Returns:
      int, A revision number from a component snapshot.  This is a int but
      formatted as an actual date in seconds (i.e 20151009132504).  It is *NOT*
      seconds since the epoch.
    """
    return int(
        time.strftime(InstallationConfig.REVISION_FORMAT_STRING, time_struct)
    )

  @staticmethod
  def ParseRevision(revision):
    """Parse the given revision into a time.struct_time.

    Args:
      revision: long, A revision number from a component snapshot.  This is a
        long int but formatted as an actual date in seconds (i.e
        20151009132504). It is *NOT* seconds since the epoch.

    Returns:
      time.struct_time, The parsed time.
    """
    return time.strptime(
        six.text_type(revision), InstallationConfig.REVISION_FORMAT_STRING
    )

  @staticmethod
  def ParseRevisionAsSeconds(revision):
    """Parse the given revision into seconds since the epoch.

    Args:
      revision: long, A revision number from a component snapshot.  This is a
        long int but formatted as an actual date in seconds (i.e
        20151009132504). It is *NOT* seconds since the epoch.

    Returns:
      int, The number of seconds since the epoch that this revision represents.
    """
    return time.mktime(InstallationConfig.ParseRevision(revision))

  def __init__(
      self,
      version,
      revision,
      user_agent,
      documentation_url,
      release_notes_url,
      snapshot_url,
      disable_updater,
      disable_usage_reporting,
      snapshot_schema_version,
      release_channel,
      config_suffix,
  ):
    # JSON returns all unicode.  We know these are regular strings and using
    # unicode in environment variables on Windows doesn't work.
    self.version = version
    self.revision = revision
    self.user_agent = str(user_agent)
    self.documentation_url = str(documentation_url)
    self.release_notes_url = str(release_notes_url)
    self.snapshot_url = str(snapshot_url)
    self.disable_updater = disable_updater
    self.disable_usage_reporting = disable_usage_reporting
    # This one is an int, no need to convert
    self.snapshot_schema_version = snapshot_schema_version
    self.release_channel = str(release_channel)
    self.config_suffix = str(config_suffix)

  def IsAlternateReleaseChannel(self):
    """Determines if this distribution is using an alternate release channel.

    Returns:
      True if this distribution is not one of the 'stable' release channels,
      False otherwise.
    """
    return self.release_channel != 'rapid'


INSTALLATION_CONFIG = InstallationConfig.Load()

CLOUD_SDK_VERSION = INSTALLATION_CONFIG.version
# TODO(b/35848109): Distribute a clientsecrets.json to avoid putting it in code.
CLOUDSDK_CLIENT_ID = '32555940559.apps.googleusercontent.com'
CLOUDSDK_CLIENT_NOTSOSECRET = 'ZmssLNjJy2998hD4CTg2ejr2'

CLOUDSDK_USER_AGENT = INSTALLATION_CONFIG.user_agent

# Do not add more scopes here.
CLOUDSDK_SCOPES = (
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/appengine.admin',
    'https://www.googleapis.com/auth/sqlservice.login',  # needed by Cloud SQL
    'https://www.googleapis.com/auth/compute',  # needed by autoscaler
)

# Do not add more scopes here.
CLOUDSDK_EXTERNAL_ACCOUNT_SCOPES = (
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/appengine.admin',
    'https://www.googleapis.com/auth/sqlservice.login',  # needed by Cloud SQL
    'https://www.googleapis.com/auth/compute',  # needed by autoscaler
)

REAUTH_SCOPE = 'https://www.googleapis.com/auth/accounts.reauth'


def EnsureSDKWriteAccess(sdk_root_override=None):
  """Error if the current user does not have write access to the sdk root.

  Args:
    sdk_root_override: str, The full path to the sdk root to use instead of
      using config.Paths().sdk_root.

  Raises:
    exceptions.RequiresAdminRightsError: If the sdk root is defined and the user
      does not have write access.
  """
  sdk_root = sdk_root_override or Paths().sdk_root
  if sdk_root and not file_utils.HasWriteAccessInDir(sdk_root):
    raise exceptions.RequiresAdminRightsError(sdk_root)


# Doesn't work in par or stub files.
def GcloudPath():
  """Gets the path the main gcloud entrypoint.

  Returns:
    str: The path to gcloud.py
  """
  return os.path.join(
      os.path.dirname(os.path.dirname(googlecloudsdk.__file__)), 'gcloud.py'
  )


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
        check_same_thread=True,  # Only creating thread may use the connection.
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

  def RowCount(self):
    return self._cursor.rowcount

  def Execute(self, *args):
    return self._cursor.execute(*args)


def GetConfigStore(config_name=None):
  """Gets the config sqlite store for a given config name.

  Args:
    config_name: string, The configuration name to get the config store for.

  Returns:
    SqliteConfigStore, The corresponding config store, or None if no config.
  """
  # Automatically defaults to active config if config_name is not specified
  if config_name is None:
    # Need try catch due to CLOUDSDK_CONFIG not writeable case, see b/290619868
    try:
      config_name = named_configs.ConfigurationStore.ActiveConfig().name
    except named_configs.NamedConfigFileAccessError:
      return None
  return _GetSqliteStore(config_name)


def _BooleanValidator(attribute_name, attribute_value):
  """Validates boolean attributes.

  Args:
    attribute_name: str, the name of the attribute
    attribute_value: str | bool, the value of the attribute to validate

  Raises:
    InvalidValueError: if value is not boolean
  """
  accepted_strings = [
      'true',
      '1',
      'on',
      'yes',
      'y',
      'false',
      '0',
      'off',
      'no',
      'n',
      '',
      'none',
  ]
  if Stringize(attribute_value).lower() not in accepted_strings:
    raise InvalidValueError(
        'The [{0}] value [{1}] is not valid. Possible values: [{2}]. '
        '(See http://yaml.org/type/bool.html)'.format(
            attribute_name,
            attribute_value,
            ', '.join([x if x else "''" for x in accepted_strings]),
        )
    )


def Stringize(value):
  if isinstance(value, six.string_types):
    return value
  return str(value)


class InvalidValueError(Error):
  """An exception to be raised when the set value of a config attribute is invalid."""


class SqliteConfigStore(object):
  """Sqlite backed config store."""

  def __init__(self, store_file, config_name):
    self._cursor = _SqlCursor(store_file)
    self._config_name = config_name
    self._Execute(
        'CREATE TABLE IF NOT EXISTS config '
        '(config_attr TEXT PRIMARY KEY, value BLOB)'
    )

  def _Execute(self, *args):
    with self._cursor as cur:
      return cur.Execute(*args)

  def _LoadAttribute(self, config_attr, required):
    """Returns the attribute value from the SQLite table."""
    loaded_config = None
    with self._cursor as cur:
      try:
        loaded_config = cur.Execute(
            'SELECT value FROM config WHERE config_attr = ?',
            (config_attr,),
        ).fetchone()
      except sqlite3.OperationalError as e:
        logging.warning(
            'Could not load config attribute [%s] in cache: %s',
            config_attr,
            str(e),
        )
    if loaded_config is None and required:
      logging.warning(
          'The required config attribute [%s] is not set.',
          config_attr,
      )
    elif loaded_config is None:
      return None

    return loaded_config[0]

  def _Load(self):
    """Returns the entire config object from the SQLite table."""
    loaded_config = None
    with self._cursor as cur:
      try:
        loaded_config = cur.Execute(
            'SELECT config_attr, value FROM config ORDER BY rowid',
        ).fetchall()
      except sqlite3.OperationalError as e:
        logging.warning(
            'Could not store config attribute in cache: %s', (str(e))
        )

    return loaded_config

  def Get(self, config_attr, required=False):
    """Gets the given attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      object, The value of the attribute, or None if it is not set.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if attr_value is None or Stringize(attr_value).lower() == 'none':
      return None
    return attr_value

  def Set(self, config_attr, config_value):
    """Sets the value for an attribute.

    Args:
      config_attr: string, the primary key of the attribute to store.
      config_value: obj, the value of the config key attribute.
    """
    if isinstance(config_value, Dict):
      config_value = json.dumps(config_value).encode('utf-8')
    self._StoreAttribute(
        config_attr,
        config_value,
    )

  def _GetBoolAttribute(self, config_attr, required, validate=True):
    """Gets the given attribute in bool form.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.
      validate: bool, True to validate the value

    Returns:
      bool, The value of the attribute, or None if it is not set.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if validate:
      _BooleanValidator(config_attr, attr_value)
    if attr_value is None:
      return None
    attr_string_value = Stringize(attr_value).lower()
    if attr_string_value == 'none':
      return None
    return attr_string_value in ['1', 'true', 'on', 'yes', 'y']

  def GetBool(self, config_attr, required=False, validate=True):
    """Gets the boolean value for this attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      bool, The boolean value for this attribute, or None if it is not set.

    Raises:
      InvalidValueError: if value is not boolean
    """
    value = self._GetBoolAttribute(config_attr, required, validate=validate)
    return value

  def _GetIntAttribute(self, config_attr, required):
    """Gets the given attribute in integer form.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      int, The integer value of the attribute, or None if it is not set.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if attr_value is None:
      return None
    try:
      return int(attr_value)
    except ValueError:
      raise InvalidValueError(
          'The attribute [{attr}] must have an integer value: [{value}]'.format(
              attr=config_attr, value=attr_value
          )
      )

  def GetInt(self, config_attr, required=False):
    """Gets the integer value for this attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      int, The integer value for this attribute.
    """
    value = self._GetIntAttribute(config_attr, required)
    return value

  def GetJSON(self, config_attr, required=False):
    """Gets the JSON value for this attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      The JSON value for this attribute or None.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if attr_value is None:
      return None
    try:
      return json.loads(attr_value)
    except ValueError:
      return attr_value

  def _StoreAttribute(self, config_attr: str, config_value):
    """Stores the input config attributes to the record of config_name in the cache.

    Args:
      config_attr: string, the primary key of the attribute to store.
      config_value: obj, the value of the config key attribute.
    """
    self._Execute(
        'REPLACE INTO config (config_attr, value) VALUES (?,?)',
        (config_attr, config_value),
    )

  def DeleteConfig(self):
    """Permanently erases the config .db file."""
    config_db_path = Paths().config_db_path.format(self._config_name)

    try:
      if os.path.exists(config_db_path):
        os.remove(config_db_path)
      else:
        logging.warning(
            'Failed to delete config DB: path [%s] does not exist.',
            config_db_path,
        )
    except OSError as e:
      logging.warning('Could not delete config from cache: %s', str(e))

  def _DeleteAttribute(self, config_attr: str):
    """Deletes a specified attribute from the config."""
    try:
      self._Execute(
          'DELETE FROM config WHERE config_attr = ?',
          (config_attr,),
      )
      # Check if deletion itself was successful
      with self._cursor as cur:
        if cur.RowCount() < 1:
          logging.warning(
              'Could not delete attribute [%s] from cache in config store'
              ' [%s].',
              config_attr,
              self._config_name,
          )

    except sqlite3.OperationalError as e:
      logging.warning(
          'Could not delete attribute [%s] from cache: %s',
          config_attr,
          str(e),
      )

  def Remove(self, config_attr):
    """Removes an attribute from the config."""
    self._DeleteAttribute(config_attr)


def _GetSqliteStore(config_name) -> SqliteConfigStore:
  """Get a sqlite-based Config Store."""
  sqlite_config_file = Paths().config_db_path.format(config_name)
  config_store = SqliteConfigStore(sqlite_config_file, config_name)
  return config_store


_CLOUDSDK_GLOBAL_CONFIG_DIR_NAME = 'gcloud' + INSTALLATION_CONFIG.config_suffix


def _GetGlobalConfigDir():
  """Returns the path to the user's global config area.

  Returns:
    str: The path to the user's global config area.
  """
  # Name of the directory that roots a cloud SDK workspace.
  global_config_dir = encoding.GetEncodedValue(os.environ, CLOUDSDK_CONFIG)
  if global_config_dir:
    return global_config_dir
  if platforms.OperatingSystem.Current() != platforms.OperatingSystem.WINDOWS:
    return os.path.join(
        file_utils.GetHomeDir(), '.config', _CLOUDSDK_GLOBAL_CONFIG_DIR_NAME
    )
  appdata = encoding.GetEncodedValue(os.environ, 'APPDATA')
  if appdata:
    return os.path.join(appdata, _CLOUDSDK_GLOBAL_CONFIG_DIR_NAME)
  # This shouldn't happen unless someone is really messing with things.
  drive = encoding.GetEncodedValue(os.environ, 'SystemDrive', 'C:')
  return os.path.join(drive, os.path.sep, _CLOUDSDK_GLOBAL_CONFIG_DIR_NAME)


class Paths(object):
  """Class to encapsulate the various directory paths of the Cloud SDK.

  Attributes:
    global_config_dir: str, The path to the user's global config area.
  """

  CLOUDSDK_STATE_DIR = '.install'
  CLOUDSDK_PROPERTIES_NAME = 'properties'

  def __init__(self):
    self.global_config_dir = _GetGlobalConfigDir()

  @property
  def sdk_root(self):
    """Searches for the Cloud SDK root directory.

    Returns:
      str, The path to the root of the Cloud SDK or None if it could not be
      found.
    """
    return file_utils.FindDirectoryContaining(
        os.path.dirname(encoding.Decode(__file__)), Paths.CLOUDSDK_STATE_DIR
    )

  @property
  def sdk_bin_path(self):
    """Forms a path to bin directory by using sdk_root.

    Returns:
      str, The path to the bin directory of the Cloud SDK or None if it could
      not be found.
    """
    sdk_root = self.sdk_root
    return os.path.join(sdk_root, 'bin') if sdk_root else None

  @property
  def cache_dir(self):
    """Gets the dir path that will contain all cache objects."""
    return os.path.join(self.global_config_dir, 'cache')

  @property
  def credentials_db_path(self):
    """Gets the path to the file to store credentials in.

    This is generic key/value store format using sqlite.

    Returns:
      str, The path to the credential db file.
    """
    return os.path.join(self.global_config_dir, 'credentials.db')

  @property
  def config_db_path(self):
    """Gets the path to the file to store configs in.

    This is generic key/value store format using sqlite.

    Returns:
      str, The path to the config db file.
    """
    return os.path.join(self.global_config_dir, '{}_configs.db')

  @property
  def access_token_db_path(self):
    """Gets the path to the file to store cached access tokens in.

    This is generic key/value store format using sqlite.

    Returns:
      str, The path to the access token db file.
    """
    return os.path.join(self.global_config_dir, 'access_tokens.db')

  @property
  def logs_dir(self):
    """Gets the path to the directory to put logs in for calliope commands.

    Returns:
      str, The path to the directory to put logs in.
    """
    return os.path.join(self.global_config_dir, 'logs')

  @property
  def cid_path(self):
    """Gets the path to the file to store the client ID.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, '.metricsUUID')

  @property
  def feature_flags_config_path(self):
    """Gets the path to the file to store the cached feature flags config file.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, '.feature_flags_config.yaml')

  @property
  def update_check_cache_path(self):
    """Gets the path to the file to cache information about update checks.

    This is stored in the config directory instead of the installation state
    because if the SDK is installed as root, it will fail to persist the cache
    when you are running gcloud as a normal user.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, '.last_update_check.json')

  @property
  def survey_prompting_cache_path(self):
    """Gets the path to the file to cache information about survey prompting.

    This is stored in the config directory instead of the installation state
    because if the SDK is installed as root, it will fail to persist the cache
    when you are running gcloud as a normal user.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, '.last_survey_prompt.yaml')

  @property
  def opt_in_prompting_cache_path(self):
    """Gets the path to the file to cache information about opt-in prompting.

    This is stored in the config directory instead of the installation state
    because if the SDK is installed as root, it will fail to persist the cache
    when you are running gcloud as a normal user.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, '.last_opt_in_prompt.yaml')

  @property
  def installation_properties_path(self):
    """Gets the path to the installation-wide properties file.

    Returns:
      str, The path to the file.
    """
    sdk_root = self.sdk_root
    if not sdk_root:
      return None
    return os.path.join(sdk_root, self.CLOUDSDK_PROPERTIES_NAME)

  @property
  def user_properties_path(self):
    """Gets the path to the properties file in the user's global config dir.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, self.CLOUDSDK_PROPERTIES_NAME)

  @property
  def named_config_activator_path(self):
    """Gets the path to the file pointing at the user's active named config.

    This is the file that stores the name of the user's active named config,
    not the path to the configuration file itself.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, 'active_config')

  @property
  def named_config_directory(self):
    """Gets the path to the directory that stores the named configs.

    Returns:
      str, The path to the directory.
    """
    return os.path.join(self.global_config_dir, 'configurations')

  @property
  def config_sentinel_file(self):
    """Gets the path to the config sentinel.

    The sentinel is a file that we touch any time there is a change to config.
    External tools can check this file to see if they need to re-query gcloud's
    credential/config helper to get updated configuration information. Nothing
    is ever written to this file, it's timestamp indicates the last time config
    was changed.

    This does not take into account config changes made through environment
    variables as they are transient by nature. There is also the edge case of
    when a user updated installation config. That user's sentinel will be
    updated but other will not be.

    Returns:
      str, The path to the sentinel file.
    """
    return os.path.join(self.global_config_dir, 'config_sentinel')

  @property
  def valid_ppk_sentinel_file(self):
    """Gets the path to the sentinel used to check for PPK encoding validity.

    The presence of this file is simply used to indicate whether or not we've
    correctly encoded the PPK used for ssh on Windows (re-encoding may be
    necessary in order to fix a bug in an older version of winkeygen.exe).

    Returns:
      str, The path to the sentinel file.
    """
    return os.path.join(self.global_config_dir, '.valid_ppk_sentinel')

  @property
  def container_config_path(self):
    """Absolute path of the container config dir."""
    return os.path.join(self.global_config_dir, 'kubernetes')

  @property
  def virtualenv_dir(self):
    """Absolute path of the virtual env dir."""
    return os.path.join(self.global_config_dir, 'virtenv')

  def LegacyCredentialsDir(self, account):
    """Gets the path to store legacy credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the credentials file.
    """
    if not account:
      account = 'default'

    # Colons in folders and filenames cause problems. Remove them.
    account = account.replace(':', '')

    # some file/directory names are reserved on Windows
    # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
    # This will handle common cases where these are email prefixes
    if (
        platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS
        and (
            account.upper().startswith('CON.')
            or account.upper().startswith('PRN.')
            or account.upper().startswith('AUX.')
            or account.upper().startswith('NUL.')
        )
    ):
      # prepend a dot to create a legal directory name
      account = '.' + account
    return os.path.join(self.global_config_dir, 'legacy_credentials', account)

  def LegacyCredentialsBqPath(self, account):
    """Gets the path to store legacy bq credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the bq credentials file.
    """
    return os.path.join(
        self.LegacyCredentialsDir(account), 'singlestore_bq.json'
    )

  def LegacyCredentialsGSUtilPath(self, account):
    """Gets the path to store legacy gsutil credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the gsutil credentials file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), '.boto')

  def LegacyCredentialsP12KeyPath(self, account):
    """Gets the path to store legacy key file in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the key file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), 'private_key.p12')

  def LegacyCredentialsAdcPath(self, account):
    """Gets the file path to store application default credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), 'adc.json')

  def GCECachePath(self):
    """Get the path to cache whether or not we're on a GCE machine.

    Returns:
      str, The path to the GCE cache.
    """
    return os.path.join(self.global_config_dir, 'gce')


def _GenerateCID(uuid_path):
  cid = uuid.uuid4().hex  # A random UUID
  file_utils.MakeDir(os.path.dirname(uuid_path))
  file_utils.WriteFileContents(uuid_path, cid)
  return cid


def GetCID():
  """Gets the client id from the config file, or generates a new one.

  Returns:
    str, The hex string of the client id.
  """
  uuid_path = Paths().cid_path
  try:
    cid = file_utils.ReadFileContents(uuid_path)
    if cid:
      return cid
  except file_utils.Error:
    pass
  return _GenerateCID(uuid_path)


def CertConfigDefaultFilePath():
  """Gets the certificate_config.json default file path.

  Returns:
    str, The default path to the config file.
    exist.
  """
  # pylint:disable=protected-access
  config_path = os.path.join(
      _cloud_sdk.get_config_path(), 'certificate_config.json'
  )
  return config_path


def ADCFilePath():
  """Gets the ADC default file path.

  Returns:
    str, The path to the default ADC file.
  """
  # pylint:disable=protected-access
  return _cloud_sdk.get_application_default_credentials_path()


def ADCEnvVariable():
  """Gets the value of the ADC environment variable.

  Returns:
    str, The value of the env var or None if unset.
  """
  return encoding.GetEncodedValue(
      os.environ, environment_vars.CREDENTIALS, None
  )
