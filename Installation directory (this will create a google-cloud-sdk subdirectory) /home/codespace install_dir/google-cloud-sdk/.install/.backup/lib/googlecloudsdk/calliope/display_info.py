# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Resource display info for the Calliope display module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.cache import cache_update_ops


class DisplayInfo(object):
  """Display info accumulator for priming Displayer.

  "legacy" logic will be dropped when the incremental Command class refactor
  is complete.

  NOTICE: If you add an attribute:
    (1) document it
    (2) handle it in AddLowerDisplayInfo()

  Attributes:
    cache_updater: A resource_cache.Updater class that will be instantiated
      and called to update the cache to reflect the resources returned by the
      calling command.
    filter: The default filter string. args.filter takes precedence.
    flatten: The default flatten string. args.flatten takes precedence.
    format: The default format string. args.format takes precedence.
    transforms: The filter/format transforms symbol dict.
    aliases: The resource name alias dict.
  """

  def __init__(self):
    self._cache_updater = None
    self._filter = None
    self._format = None
    self._flatten = None
    self._transforms = {}
    self._aliases = {}

  # pylint: disable=redefined-builtin, name matches args.format and --format
  def AddLowerDisplayInfo(self, display_info):
    """Add lower precedence display_info to the object.

    This method is called by calliope to propagate CLI low precedence parent
    info to its high precedence children.

    Args:
      display_info: The low precedence DisplayInfo object to add.
    """
    if not self._cache_updater:
      self._cache_updater = display_info.cache_updater
    if not self._filter:
      self._filter = display_info.filter
    if not self._format:
      self._format = display_info.format
    if not self._flatten:
      self._flatten = display_info.flatten
    if display_info.transforms:
      transforms = dict(display_info.transforms)
      transforms.update(self.transforms)
      self._transforms = transforms
    if display_info.aliases:
      aliases = dict(display_info.aliases)
      aliases.update(self._aliases)
      self._aliases = aliases

  def AddFormat(self, format):
    """Adds a format to the display info, newer info takes precedence.

    Args:
      format: The default format string. args.format takes precedence.
    """
    if format:
      self._format = format

  def AddFlatten(self, flatten):
    """Adds a flatten to the display info, newer info takes precedence.

    Args:
      flatten: [str], The list of flatten strings to use by default; e.g.
        ['fieldA.fieldB', 'fieldC.fieldD']. Flatten strings provided by
        args.flatten take precedence if the --flatten flag is specified.
    """
    if flatten:
      self._flatten = flatten

  def AddFilter(self, filter):
    """Adds a filter to the display info, newer info takes precedence.

    Args:
      filter: The default filter string. args.filter takes precedence.
    """
    if filter:
      self._filter = filter

  def AddTransforms(self, transforms):
    """Adds transforms to the display info, newer values takes precedence.

    Args:
      transforms: A filter/format transforms symbol dict.
    """
    if transforms:
      self._transforms.update(transforms)

  def AddUriFunc(self, uri_func):
    """Adds a uri transform to the display info using uri_func.

    Args:
      uri_func: func(resource), A function that returns the uri for a
        resource object.
    """
    def _TransformUri(resource, undefined=None):
      try:
        return uri_func(resource) or undefined
      except (AttributeError, TypeError):
        return undefined

    self.AddTransforms({'uri': _TransformUri})

  def AddAliases(self, aliases):
    """Adds aliases to the display info, newer values takes precedence.

    Args:
      aliases: {str: parsed_key} The resource name alias dict that maps short
        names to parsed keys. The parsed key for 'abc.xyz' is ['abc', 'xyz'].
        See the resource_lex.Lexer.Key() docstring for parsed key details.
    """
    if aliases:
      self._aliases.update(aliases)

  def AddCacheUpdater(self, cache_updater):
    """Adds a cache_updater to the display info, newer values takes precedence.

    The cache updater is called to update the resource cache for CreateCommand,
    DeleteCommand and ListCommand commands.

    Args:
      cache_updater: A resource_cache.Updater class that will be instantiated
        and called to update the cache to reflect the resources returned by the
        calling command. None disables cache update.
    """
    self._cache_updater = cache_updater or cache_update_ops.NoCacheUpdater

  @property
  def cache_updater(self):
    return self._cache_updater

  @property
  def format(self):
    return self._format

  @property
  def flatten(self):
    return self._flatten

  @property
  def filter(self):
    return self._filter

  @property
  def aliases(self):
    return self._aliases

  @property
  def transforms(self):
    return self._transforms
