# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Support functions for the handling of named configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import os
import re
import threading

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.configurations import properties_file
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils

# The special configuration named NONE contains no properties
_NO_ACTIVE_CONFIG_NAME = 'NONE'
_RESERVED_CONFIG_NAMES = (_NO_ACTIVE_CONFIG_NAME,)
# This will be created by default when there are no configurations present.
DEFAULT_CONFIG_NAME = 'default'

_VALID_CONFIG_NAME_REGEX = r'^[a-z][-a-z0-9]*$'
_CONFIG_FILE_PREFIX = 'config_'
_CONFIG_FILE_REGEX = r'^config_([a-z][-a-z0-9]*)$'


class Error(exceptions.Error):
  """Base class for errors handling named configurations."""


class NamedConfigError(Error):
  """Errors when dealing with operations on configurations."""


class NamedConfigFileAccessError(NamedConfigError):
  """Raise for errors dealing with file access errors."""

  def __init__(self, message, exc):
    super(NamedConfigFileAccessError, self).__init__('{0}.\n  {1}'.format(
        message, getattr(exc, 'strerror', exc)))


class InvalidConfigName(NamedConfigError):
  """Raise to indicate an invalid named config name."""

  def __init__(self, bad_name):
    super(InvalidConfigName, self).__init__(
        'Invalid name [{0}] for a configuration.  Except for special cases '
        '({1}), configuration names start with a lower case letter and '
        'contain only lower case letters a-z, digits 0-9, '
        'and hyphens \'-\'.'.format(bad_name, ','.join(_RESERVED_CONFIG_NAMES)))


class ReadOnlyConfigurationError(Error):
  """An exception for when the active config is read-only (e.g. None)."""

  def __init__(self, config_name):
    super(ReadOnlyConfigurationError, self).__init__(
        'Properties in configuration [{0}] cannot be set.'.format(config_name))


class _FlagOverrideStack(object):
  """Class representing a stack of configuration flag values or `None`s.

  Each time a command line is parsed (the original, and any from commands
  calling other commands internally), the new value for the --configuration
  flag is added to the top of the stack (if it is provided).  This is used for
  resolving the currently active configuration.

  We need to do quick parsing of the args here because things like logging are
  used before argparse parses the command line and logging needs properties.
  We scan the command line for the --configuration flag to get the active
  configuration before any of that starts.
  """

  def __init__(self):
    self._stack = []

  def Push(self, config_flag):
    """Add a new value to the top of the stack."""
    old_flag = self.ActiveConfig()
    self._stack.append(config_flag)
    if old_flag != config_flag:
      ActivePropertiesFile.Invalidate()

  def PushFromArgs(self, args):
    """Parse the args and add the value that was found to the top of the stack.

    Args:
      args: [str], The command line args for this invocation.
    """
    self.Push(_FlagOverrideStack._FindFlagValue(args))

  def Pop(self):
    """Remove the top value from the stack."""
    return self._stack.pop()

  def ActiveConfig(self):
    """Get the top most value on the stack."""
    for value in reversed(self._stack):
      if value:
        return value
    return None

  @classmethod
  def _FindFlagValue(cls, args):
    """Parse the given args to find the value of the --configuration flag.

    Args:
      args: [str], The arguments from the command line to parse

    Returns:
      str, The value of the --configuration flag or None if not found.
    """
    flag = '--configuration'
    flag_eq = flag + '='

    successor = None
    config_flag = None

    # Try to parse arguments going right to left(!).  This is so that if
    # if a user runs someone does
    #    $ alias g=gcloud --configuration foo compute
    #    $ g --configuration bar ssh
    # we'll pick up configuration bar instead of foo.
    for arg in reversed(args):
      if arg == flag:
        config_flag = successor
        break
      if arg.startswith(flag_eq):
        _, config_flag = arg.split('=', 1)
        break
      successor = arg

    return config_flag


FLAG_OVERRIDE_STACK = _FlagOverrideStack()


class ConfigurationStore(object):
  """Class for performing low level operations on configs and their files."""

  @staticmethod
  def ActiveConfig():
    """Gets the currently active configuration.

    There must always be an active configuration.  If there isn't this means
    no configurations have been created yet and this will auto-create a default
    configuration.  If there are legacy user properties, they will be migrated
    to the newly created configuration.

    Returns:
      Configuration, the currently active configuration.
    """
    return ActiveConfig(force_create=True)

  @staticmethod
  def AllConfigs(include_none_config=False):
    """Returns all the configurations that exist.

    This determines the currently active configuration so as a side effect it
    will create the default configuration if no configurations exist.

    Args:
      include_none_config: bool, True to include the NONE configuration in the
        list. This is a reserved configuration that indicates to not use any
        configuration.  It is not explicitly created but is always available.

    Returns:
      {str, Configuration}, A map of configuration name to the configuration
      object.
    """
    config_dir = config.Paths().named_config_directory

    active_config = ConfigurationStore.ActiveConfig()
    active_config_name = active_config.name

    configs = {}
    if include_none_config:
      configs[_NO_ACTIVE_CONFIG_NAME] = Configuration(
          _NO_ACTIVE_CONFIG_NAME, _NO_ACTIVE_CONFIG_NAME == active_config_name)

    try:
      config_files = os.listdir(config_dir)
      for f in config_files:
        m = re.match(_CONFIG_FILE_REGEX, f)
        if m:
          name = m.group(1)
          configs[name] = Configuration(name, name == active_config_name)
      return configs
    except (OSError, IOError) as exc:
      if exc.errno != errno.ENOENT:
        raise NamedConfigFileAccessError(
            'List of configurations could not be read from: [{0}]'.format(
                config_dir), exc)
    return {}

  @staticmethod
  def CreateConfig(config_name):
    """Creates a configuration with the given name.

    Args:
      config_name: str, The name of the configuration to create.

    Returns:
      Configuration, The configuration that was just created.

    Raises:
      NamedConfigError: If the configuration already exists.
      NamedConfigFileAccessError: If there a problem manipulating the
        configuration files.
    """
    _EnsureValidConfigName(config_name, allow_reserved=False)

    paths = config.Paths()
    file_path = _FileForConfig(config_name, paths)
    if os.path.exists(file_path):
      raise NamedConfigError(
          'Cannot create configuration [{0}], it already exists.'
          .format(config_name))

    try:
      file_utils.MakeDir(paths.named_config_directory)
      file_utils.WriteFileContents(file_path, '')
    except file_utils.Error as e:
      raise NamedConfigFileAccessError(
          'Failed to create configuration [{0}].  Ensure you have the correct '
          'permissions on [{1}]'.format(config_name,
                                        paths.named_config_directory), e)

    return Configuration(config_name, is_active=False)

  @staticmethod
  def DeleteConfig(config_name):
    """Creates the given configuration.

    Args:
      config_name: str, The name of the configuration to delete.

    Raises:
      NamedConfigError: If the configuration does not exist.
      NamedConfigFileAccessError: If there a problem manipulating the
        configuration files.
    """
    _EnsureValidConfigName(config_name, allow_reserved=False)

    paths = config.Paths()
    file_path = _FileForConfig(config_name, paths)
    if not os.path.exists(file_path):
      raise NamedConfigError(
          'Cannot delete configuration [{0}], it does not exist.'
          .format(config_name))

    # Check if it is effectively the active one, or even if it is overridden by
    # env or flags, make sure it is not set as active in the file.
    if config_name == _EffectiveActiveConfigName():
      raise NamedConfigError(
          'Cannot delete configuration [{0}], it is the currently active '
          'configuration.'.format(config_name))
    if config_name == _ActiveConfigNameFromFile():
      raise NamedConfigError(
          'Cannot delete configuration [{0}], it is currently set as the active'
          ' configuration in your gcloud properties.'.format(config_name))

    try:
      os.remove(file_path)
    except (OSError, IOError) as e:
      raise NamedConfigFileAccessError(
          'Failed to delete configuration [{0}].  Ensure you have the correct '
          'permissions on [{1}]'.format(config_name,
                                        paths.named_config_directory), e)

  @staticmethod
  def ActivateConfig(config_name):
    """Activates an existing named configuration.

    Args:
      config_name: str, The name of the configuration to activate.

    Raises:
      NamedConfigError: If the configuration does not exists.
      NamedConfigFileAccessError: If there a problem manipulating the
        configuration files.
    """
    _EnsureValidConfigName(config_name, allow_reserved=True)

    paths = config.Paths()
    file_path = _FileForConfig(config_name, paths)
    if file_path and not os.path.exists(file_path):
      raise NamedConfigError(
          'Cannot activate configuration [{0}], it does not exist.'
          .format(config_name))

    try:
      file_utils.WriteFileContents(
          paths.named_config_activator_path, config_name)
    except file_utils.Error as e:
      raise NamedConfigFileAccessError(
          'Failed to activate configuration [{0}].  Ensure you have the '
          'correct permissions on [{1}]'.format(
              config_name, paths.named_config_activator_path),
          e)

    ActivePropertiesFile.Invalidate(mark_changed=True)

  @staticmethod
  def RenameConfig(config_name, new_name):
    """Renames an existing named configuration.

    Args:
      config_name: str, The name of the configuration to rename.
      new_name: str, The new name of the configuration.

    Raises:
      NamedConfigError: If the configuration does not exist, or if the
        configuration with new_name exists.
      NamedConfigFileAccessError: If there a problem manipulating the
        configuration files.
    """
    _EnsureValidConfigName(new_name, allow_reserved=True)
    paths = config.Paths()
    file_path = _FileForConfig(config_name, paths)
    if file_path and not os.path.exists(file_path):
      raise NamedConfigError(
          'Cannot rename configuration [{0}], it does not exist.'
          .format(config_name))

    # Check if it is effectively the active one, or even if it is overridden by
    # env or flags, make sure it is not set as active in the file.
    if config_name == _EffectiveActiveConfigName():
      raise NamedConfigError(
          'Cannot rename configuration [{0}], it is the currently active '
          'configuration.'.format(config_name))
    if config_name == _ActiveConfigNameFromFile():
      raise NamedConfigError(
          'Cannot rename configuration [{0}], it is currently set as the active'
          ' configuration in your gcloud properties.'.format(config_name))

    new_file_path = _FileForConfig(new_name, paths)
    if new_file_path and os.path.exists(new_file_path):
      raise NamedConfigError(
          'Cannot rename configuration [{0}], [{1}] already exists.'
          .format(config_name, new_name))

    # Copy contents over and delete old config
    try:
      contents = file_utils.ReadFileContents(file_path)
      file_utils.WriteFileContents(new_file_path, contents)
      os.remove(file_path)
    except file_utils.Error as e:
      # pylint: disable=raise-missing-from
      raise NamedConfigFileAccessError(
          'Failed to rename configuration [{0}].  Ensure you have the '
          'correct permissions on [{1}]'.format(
              config_name, paths.named_config_activator_path),
          e)


class Configuration(object):
  """A class to encapsulate a single configuration."""

  def __init__(self, name, is_active):
    self.name = name
    self.is_active = is_active
    self.file_path = _FileForConfig(name, config.Paths())

  def GetProperties(self):
    """Gets the properties defined in this configuration.

    These are the properties literally defined in this file, not the effective
    properties based on other configs or the environment.

    Returns:
      {str, str}, A dictionary of all properties defined in this configuration
      file.
    """
    if not self.file_path:
      return {}
    return properties_file.PropertiesFile([self.file_path]).AllProperties()

  def PersistProperty(self, section, name, value):
    """Persists a property to this configuration file.

    Args:
      section: str, The section name of the property to set.
      name: str, The name of the property to set.
      value: str, The value to set for the given property, or None to unset it.

    Raises:
      ReadOnlyConfigurationError: If you are trying to persist properties to
        the None configuration.
      NamedConfigError: If the configuration does not exist.
    """
    if not self.file_path:
      raise ReadOnlyConfigurationError(self.name)

    if not os.path.exists(self.file_path):
      raise NamedConfigError(
          'Cannot set property in configuration [{0}], it does not exist.'
          .format(self.name))

    properties_file.PersistProperty(self.file_path, section, name, value)
    if self.is_active:
      ActivePropertiesFile.Invalidate(mark_changed=True)

  def Activate(self):
    """Mark this configuration as active in the activator file."""
    return ConfigurationStore.ActivateConfig(self.name)


class ActivePropertiesFile(object):
  """An interface for loading and caching the active properties from file."""

  _PROPERTIES = None
  _LOCK = threading.RLock()

  @staticmethod
  def Load():
    """Loads the set of active properties from file.

    This includes both the installation configuration as well as the currently
    active configuration file.

    Returns:
      properties_file.PropertiesFile, The CloudSDK properties.
    """
    ActivePropertiesFile._LOCK.acquire()
    try:
      if not ActivePropertiesFile._PROPERTIES:
        ActivePropertiesFile._PROPERTIES = properties_file.PropertiesFile(
            [config.Paths().installation_properties_path, ActiveConfig(
                force_create=False).file_path])
    finally:
      ActivePropertiesFile._LOCK.release()
    return ActivePropertiesFile._PROPERTIES

  @staticmethod
  def Invalidate(mark_changed=False):
    """Invalidate the cached property values.

    Args:
      mark_changed: bool, True if we are invalidating because we persisted
        a change to the installation config, the active configuration, or
        changed the active configuration. If so, the config sentinel is touched.
    """
    ActivePropertiesFile._PROPERTIES = None
    if mark_changed:
      file_utils.WriteFileContents(config.Paths().config_sentinel_file, '')


def ActiveConfig(force_create):
  """Gets the currently active configuration.

  There must always be an active configuration.  If there isn't this means
  no configurations have been created yet and this will auto-create a default
  configuration.  If there are legacy user properties, they will be migrated
  to the newly created configuration.

  Args:
    force_create: bool, If False and if there are no legacy properties, the
      new default configuration won't actually be created.  We just pretend
      that it exists, which is sufficient since it is empty.  We do this to
      avoid always creating the configuration when properties are just trying
      to be read.  This should only be set to False when seeing a
      PropertiesFile object.  All other operations must actually create the
      configuration.

  Returns:
    Configuration, the currently active configuration.
  """
  config_name = _EffectiveActiveConfigName()

  # No configurations have ever been created
  if not config_name:
    config_name = _CreateDefaultConfig(force_create)

  return Configuration(config_name, True)


def _EffectiveActiveConfigName():
  """Gets the currently active configuration.

  It checks (in order):
    - Flag values
    - Environment variable values
    - The value set in the activator file

  Returns:
    str, The name of the active configuration or None if no location declares
    an active configuration.
  """
  config_name = FLAG_OVERRIDE_STACK.ActiveConfig()
  if not config_name:
    config_name = _ActiveConfigNameFromEnv()
  if not config_name:
    config_name = _ActiveConfigNameFromFile()
  return config_name


def _ActiveConfigNameFromEnv():
  """Gets the currently active configuration according to the environment.

  Returns:
    str, The name of the active configuration or None.
  """
  return encoding.GetEncodedValue(
      os.environ, config.CLOUDSDK_ACTIVE_CONFIG_NAME, None)


def _ActiveConfigNameFromFile():
  """Gets the name of the user's active named config according to the file.

  Returns:
    str, The name of the active configuration or None.
  """
  path = config.Paths().named_config_activator_path
  is_invalid = False

  try:
    config_name = file_utils.ReadFileContents(path)
    # If the file is empty, treat it like the file does not exist.
    if config_name:
      if _IsValidConfigName(config_name, allow_reserved=True):
        return config_name
      else:
        # Somehow the file got corrupt, just remove it and it will get
        # recreated correctly.
        is_invalid = True
  except file_utils.MissingFileError:
    pass
  except file_utils.Error as exc:
    raise NamedConfigFileAccessError(
        'Active configuration name could not be read from: [{0}]. Ensure you '
        'have sufficient read permissions on required active configuration '
        'in [{1}]'
        .format(path, config.Paths().named_config_directory), exc)

  if is_invalid:
    os.remove(path)
  # The active named config pointer file is missing, return None
  return None


def _FileForConfig(config_name, paths):
  """Gets the path to the properties file for a given configuration.

  The file need not actually exist, it is just the path where it would be.

  Args:
    config_name: str, The name of the configuration.
    paths: config.Paths, The instantiated Paths object to use to calculate the
      location.

  Returns:
    str, The path to the file or None if this configuration does not have a
    corresponding file.
  """
  if config_name == _NO_ACTIVE_CONFIG_NAME:
    return None
  return os.path.join(paths.named_config_directory,
                      _CONFIG_FILE_PREFIX + config_name)


def _IsValidConfigName(config_name, allow_reserved):
  """Determines if the given configuration name conforms to the standard.

  Args:
    config_name: str, The name to check.
    allow_reserved: bool, Allows the given name to be one of the reserved
      configuration names.

  Returns:
    True if valid, False otherwise.
  """
  if config_name in _RESERVED_CONFIG_NAMES:
    if not allow_reserved:
      return False
  elif not re.match(_VALID_CONFIG_NAME_REGEX, config_name):
    return False
  return True


def _EnsureValidConfigName(config_name, allow_reserved):
  """Ensures that the given configuration name conforms to the standard.

  Args:
    config_name: str, The name to check.
    allow_reserved: bool, Allows the given name to be one of the reserved
      configuration names.

  Raises:
    InvalidConfigName: If the name is invalid.
  """
  if not _IsValidConfigName(config_name, allow_reserved):
    raise InvalidConfigName(config_name)


def _CreateDefaultConfig(force_create):
  """Create the default configuration and migrate legacy properties.

  This will only do anything if there are no existing configurations.  If that
  is true, it will create one called default.  If there are existing legacy
  properties, it will populate the new configuration with those settings.
  The old file will be marked as deprecated.

  Args:
    force_create: bool, If False and no legacy properties exist to be migrated
      this will not physically create the default configuration.  This is ok
      as long as we are strictly reading properties from this configuration.

  Returns:
    str, The default configuration name.
  """
  paths = config.Paths()
  try:
    if not os.path.exists(paths.named_config_activator_path):
      # No configurations exist yet.  If there are legacy properties, we need
      # to create the configuration now and seed with those properties.  If no
      # legacy properties, only create the configuration if force_create is
      # True.
      legacy_properties = _GetAndDeprecateLegacyProperties(paths)
      if legacy_properties or force_create:
        file_utils.MakeDir(paths.named_config_directory)
        target_file = _FileForConfig(DEFAULT_CONFIG_NAME, paths)
        file_utils.WriteFileContents(target_file, legacy_properties)
        file_utils.WriteFileContents(paths.named_config_activator_path,
                                     DEFAULT_CONFIG_NAME)
  except file_utils.Error as e:
    raise NamedConfigFileAccessError(
        'Failed to create the default configuration. Ensure your have the '
        'correct permissions on: [{0}]'.format(paths.named_config_directory), e)
  return DEFAULT_CONFIG_NAME


_LEGACY_DEPRECATION_MESSAGE = """\
# This properties file has been superseded by named configurations.
# Editing it will have no effect.

"""


def _GetAndDeprecateLegacyProperties(paths):
  """Gets the contents of the legacy  properties to include in a new config.

  If the properties have already been imported, this returns nothing.  If not,
  this will return the old properties and mark the old file as deprecated.

  Args:
    paths: config.Paths, The instantiated Paths object to use to calculate the
      location.

  Returns:
    str, The contents of the legacy properties file or ''.
  """
  contents = ''

  if os.path.exists(paths.user_properties_path):
    contents = file_utils.ReadFileContents(paths.user_properties_path)
    if contents.startswith(_LEGACY_DEPRECATION_MESSAGE):
      # We have already migrated these properties, the user must have
      # deleted all their configurations.  Don't migrate again.
      contents = ''
    else:
      file_utils.WriteFileContents(paths.user_properties_path,
                                   _LEGACY_DEPRECATION_MESSAGE + contents)

  return contents
