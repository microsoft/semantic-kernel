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

"""The meta cache command library support."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.calliope import parser_completer
from googlecloudsdk.calliope import walker
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import module_util
from googlecloudsdk.core import resources
from googlecloudsdk.core.cache import exceptions as cache_exceptions
from googlecloudsdk.core.cache import file_cache
from googlecloudsdk.core.cache import resource_cache

import six


_CACHE_RI_DEFAULT = 'resource://'


class Error(exceptions.Error):
  """Base cache exception."""


class NoTablesMatched(Error):
  """No table names matched the patterns."""


class GetCache(object):
  """Context manager for opening a cache given a cache identifier name."""

  _TYPES = {
      'file': file_cache.Cache,
      'resource': resource_cache.ResourceCache,
  }

  def __init__(self, name, create=False):
    """Constructor.

    Args:
      name: The cache name to operate on. May be prefixed by "resource://" for
        resource cache names or "file://" for persistent file cache names. If
        only the prefix is specified then the default cache name for that prefix
        is used.
      create: Creates the persistent cache if it exists if True.

    Raises:
      CacheNotFound: If the cache does not exist.

    Returns:
      The cache object.
    """
    self._name = name
    self._create = create
    self._cache = None

  def _OpenCache(self, cache_class, name):
    try:
      return cache_class(name, create=self._create)
    except cache_exceptions.Error as e:
      raise Error(e)

  def __enter__(self):
    # Each cache_class has a default cache name. None or '' names that default.
    if self._name:
      for cache_id, cache_class in six.iteritems(self._TYPES):
        if self._name.startswith(cache_id + '://'):
          name = self._name[len(cache_id) + 3:]
          if not name:
            name = None
          self._cache = self._OpenCache(cache_class, name)
          return self._cache
    self._cache = self._OpenCache(resource_cache.ResourceCache, self._name)
    return self._cache

  def __exit__(self, typ, value, traceback):
    self._cache.Close(commit=typ is None)


def Delete():
  """Deletes the resource cache regardless of implementation."""
  try:
    resource_cache.Delete()
  except cache_exceptions.Error as e:
    raise Error(e)
  return None


def AddCacheFlag(parser):
  """Adds the persistent cache flag to the parser."""
  parser.add_argument(
      '--cache',
      metavar='CACHE_NAME',
      default=_CACHE_RI_DEFAULT,
      help=('The cache name to operate on. May be prefixed by "{}" for '
            'resource cache names. If only the prefix is specified then the '
            'default cache name for that prefix is used.'.format(
                _CACHE_RI_DEFAULT)))


def _GetCompleterType(completer_class):
  """Returns the completer type name given its class."""
  completer_type = None
  try:
    for t in completer_class.mro():
      if t == completers.ResourceCompleter:
        break
      if t.__name__.endswith('Completer'):
        completer_type = t.__name__
  except AttributeError:
    pass
  if not completer_type and callable(completer_class):
    completer_type = 'function'
  return completer_type


class _CompleterModule(object):

  def __init__(self, module_path, collection, api_version, completer_type):
    self.module_path = module_path
    self.collection = collection
    self.api_version = api_version
    self.type = completer_type
    self.attachments = []
    self._attachments_dict = {}


class _CompleterAttachment(object):

  def __init__(self, command):
    self.command = command
    self.arguments = []


class _CompleterModuleGenerator(walker.Walker):
  """Constructs a CLI command dict tree."""

  def __init__(self, cli):
    super(_CompleterModuleGenerator, self).__init__(cli)
    self._modules_dict = {}

  def Visit(self, command, parent, is_group):
    """Visits each command in the CLI command tree to construct the module list.

    Args:
      command: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if command is a group, otherwise its is a command.

    Returns:
      The subtree module list.
    """

    def _ActionKey(action):
      return action.__repr__()

    args = command.ai
    for arg in sorted(args.flag_args + args.positional_args, key=_ActionKey):
      try:
        completer_class = arg.completer
      except AttributeError:
        continue
      collection = None
      api_version = None
      if isinstance(completer_class, parser_completer.ArgumentCompleter):
        completer_class = completer_class.completer_class
      module_path = module_util.GetModulePath(completer_class)
      if isinstance(completer_class, type):
        try:
          completer = completer_class()
          try:
            collection = completer.collection
          except AttributeError:
            pass
          try:
            api_version = completer.api_version
          except AttributeError:
            pass
        except (apis_util.UnknownAPIError,
                resources.InvalidCollectionException) as e:
          collection = 'ERROR: {}'.format(e)
      if arg.option_strings:
        name = arg.option_strings[0]
      else:
        name = arg.dest.replace('_', '-')
      module = self._modules_dict.get(module_path)
      if not module:
        module = _CompleterModule(
            module_path=module_path,
            collection=collection,
            api_version=api_version,
            completer_type=_GetCompleterType(completer_class),
        )
        self._modules_dict[module_path] = module
      command_path = ' '.join(command.GetPath())
      # pylint: disable=protected-access
      attachment = module._attachments_dict.get(command_path)
      if not attachment:
        attachment = _CompleterAttachment(command_path)
        module._attachments_dict[command_path] = attachment
        module.attachments.append(attachment)
      attachment.arguments.append(name)
    return self._modules_dict


def ListAttachedCompleters(cli):
  """Returns the list of all attached CompleterModule objects in cli."""
  return list(_CompleterModuleGenerator(cli).Walk().values())
