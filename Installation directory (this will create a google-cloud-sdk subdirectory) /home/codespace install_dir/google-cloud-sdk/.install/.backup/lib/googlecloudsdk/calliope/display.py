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
"""Resource display for all calliope commands.

The print_format string passed to resource_printer.Print() is determined in this
order:
 (1) Display disabled and resources not consumed if user output is disabled.
 (2) The explicit --format flag format string.
 (3) The explicit Display() method.
 (4) The DisplayInfo format from the parser.
 (5) Otherwise no output but the resources are consumed.

Format expressions are left-to-right composable. Each format expression is a
string tuple

  < NAME [ATTRIBUTE...] (PROJECTION...) >

where only one of the three elements need be present.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import display_taps
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import module_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.cache import cache_update_ops
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.resource import resource_reference
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import peek_iterable
import six


class Error(exceptions.Error):
  """Base exception for this module."""


class CommandNeedsAddCacheUpdater(Error):
  """Command needs an AddCacheUpdater() call."""


class CommandShouldntHaveAddCacheUpdater(Error):
  """Command has an AddCacheUpdater() call and shouldn't."""


class Displayer(object):
  """Implements the resource display method.

  Dispatches the global flags args by constructing a format string and letting
  resource_printer.Print() do the heavy lifting.

  Attributes:
    _args: The argparse.Namespace given to command.Run().
    _command: The Command object that generated the resources to display.
    _defaults: The resource format and filter default projection.
    _format: The printer format string.
    _info: The resource info or None if not registered.
    _printer: The printer object.
    _printer_is_initialized: True if self._printer has been initialized.
    _resources: The resources to display, returned by command.Run().
    _transform_uri: A transform function that returns the URI for a resource.
  """

  # A command with these flags might return incomplete resource lists.
  _CORRUPT_FLAGS = ('async', 'filter', 'limit')

  def __init__(self, command, args, resources=None, display_info=None):
    """Constructor.

    Args:
      command: The Command object.
      args: The argparse.Namespace given to the command.Run().
      resources: The resources to display, returned by command.Run(). May be
        omitted if only GetFormat() will be called.
      display_info: The DisplayInfo object reaped from parser.AddDisplayInfo()
        in the command path.
    """
    self._args = args
    self._cache_updater = None
    self._command = command
    self._defaults = None
    self._default_format_used = False
    self._format = None
    self._filter = None
    self._info = None
    self._printer = None
    self._printer_is_initialized = False
    self._resources = resources
    if not display_info:
      # pylint: disable=protected-access
      display_info = args.GetDisplayInfo()
    if display_info:
      self._cache_updater = display_info.cache_updater
      self._defaults = resource_projection_spec.ProjectionSpec(
          defaults=self._defaults,
          symbols=display_info.transforms,
          aliases=display_info.aliases)
      self._format = display_info.format
      self._flatten = display_info.flatten
      self._filter = display_info.filter
    self._transform_uri = self._defaults.symbols.get(
        'uri', resource_transform.TransformUri)
    self._defaults.symbols[
        resource_transform.GetTypeDataName('conditionals')] = args

  def _GetFlag(self, flag_name):
    """Returns the value of flag_name in args, None if it is unknown or unset.

    Args:
      flag_name: The flag name string sans leading '--'.

    Returns:
      The flag value or None if it is unknown or unset.
    """
    if flag_name == 'async':
      # The async flag has a special destination since 'async' is a reserved
      # keyword as of Python 3.7.
      return getattr(self._args, 'async_', None)
    return getattr(self._args, flag_name, None)

  def _AddUriCacheTap(self):
    """Taps a resource Uri cache updater into self.resources if needed."""

    from googlecloudsdk.calliope import base  # pylint: disable=g-import-not-at-top, circular dependency

    if self._cache_updater == cache_update_ops.NoCacheUpdater:
      return

    if not self._cache_updater:
      # pylint: disable=protected-access
      if not isinstance(self._command,
                        (base.CreateCommand,
                         base.DeleteCommand,
                         base.ListCommand,
                         base.RestoreCommand)):
        return
      if 'AddCacheUpdater' in properties.VALUES.core.lint.Get():
        # pylint: disable=protected-access
        raise CommandNeedsAddCacheUpdater(
            '`{}` needs a parser.display_info.AddCacheUpdater() call.'.format(
                ' '.join(self._args._GetCommand().GetPath())))
      return

    if any([self._GetFlag(flag) for flag in self._CORRUPT_FLAGS]):
      return

    # pylint: disable=protected-access
    if isinstance(self._command, (base.CreateCommand, base.RestoreCommand)):
      cache_update_op = cache_update_ops.AddToCacheOp(self._cache_updater)
    elif isinstance(self._command, base.DeleteCommand):
      cache_update_op = cache_update_ops.DeleteFromCacheOp(self._cache_updater)
    elif isinstance(self._command, base.ListCommand):
      cache_update_op = cache_update_ops.ReplaceCacheOp(self._cache_updater)
    else:
      raise CommandShouldntHaveAddCacheUpdater(
          'Cache updater [{}] not expected for [{}] `{}`.'.format(
              module_util.GetModulePath(self._cache_updater),
              module_util.GetModulePath(self._args._GetCommand()),
              ' '.join(self._args._GetCommand().GetPath())))

    tap = display_taps.UriCacher(cache_update_op, self._transform_uri)
    self._resources = peek_iterable.Tapper(self._resources, tap)

  def _GetSortKeys(self):
    """Returns the list of --sort-by [(key, reverse)] tuples.

    Returns:
      The list of --sort-by [(key, reverse)] tuples, None if --sort-by was not
      specified. The keys are ordered from highest to lowest precedence.
    """
    if not self._GetFlag('sort_by'):
      return None
    keys = []
    for name in self._args.sort_by:
      # ~name reverses the sort for name.
      if name.startswith('~'):
        name = name.lstrip('~')
        reverse = True
      else:
        reverse = False
      # Slices default to the first list element for consistency.
      name = name.replace('[]', '[0]')
      keys.append((resource_lex.Lexer(name).Key(), reverse))
    return keys

  def _SortResources(self, keys, reverse):
    """_AddSortByTap helper that sorts the resources by keys.

    Args:
      keys: The ordered list of parsed resource keys from highest to lowest
        precedence.
      reverse: Sort by the keys in descending order if True, otherwise
        ascending.
    """
    def _GetKey(r, key):
      """Returns the value for key in r that can be compared with None."""
      value = resource_property.Get(r, key, None)
      # Some types (datetime for example) preclude comparisons with None.
      # This converts the value to a string and uses that ordering.
      try:
        assert None < value
        return value
      except (AssertionError, TypeError):
        return six.text_type(value)

    self._resources = sorted(
        self._resources,
        key=lambda r: [_GetKey(r, k) for k in keys],
        reverse=reverse)

  def _AddSortByTap(self):
    """Sorts the resources using the --sort-by keys."""
    if not resource_property.IsListLike(self._resources):
      return
    sort_keys = self._GetSortKeys()
    if not sort_keys:
      return
    self._args.sort_by = None
    # This loop partitions the keys into groups having the same reverse value.
    # The groups are then applied in reverse order to maintain the original
    # precedence.
    #
    # This is not a pure tap since, by necessity, it consumes self._resources
    # to sort and converts it to a list.
    groups = []  # [(group_keys, group_reverse)] LIFO to preserve precedence
    group_keys = []  # keys for current group
    group_reverse = False
    for key, reverse in sort_keys:
      if not group_keys:
        group_reverse = reverse
      elif group_reverse != reverse:
        groups.insert(0, (group_keys, group_reverse))
        group_keys = []
        group_reverse = reverse
      group_keys.append(key)
    if group_keys:
      groups.insert(0, (group_keys, group_reverse))

    # Finally sort the resources by groups having the same reverse value.
    for keys, reverse in groups:
      self._SortResources(keys, reverse)

  def _AddFilterTap(self):
    """Taps a resource filter into self.resources if needed."""
    expression = self._GetFilter()
    if not expression:
      return
    tap = display_taps.Filterer(expression, self._defaults)
    self._resources = peek_iterable.Tapper(self._resources, tap)

  def _AddFlattenTap(self):
    """Taps one or more resource flatteners into self.resources if needed."""

    def _Slice(key):
      """Helper to add one flattened slice tap."""
      tap = display_taps.Flattener(key)
      # Apply the flatteners from left to right so the innermost flattener
      # flattens the leftmost slice. The outer flatteners can then access
      # the flattened keys to the left.
      self._resources = peek_iterable.Tapper(self._resources, tap)

    keys = self._GetFlatten()
    if not keys:
      return
    for key in keys:
      flattened_key = []
      sliced = False
      for k in resource_lex.Lexer(key).Key():
        if k is None:
          sliced = True
          _Slice(flattened_key)
        else:
          sliced = False
          flattened_key.append(k)
      if not sliced:
        _Slice(flattened_key)

  def _AddLimitTap(self):
    """Taps a resource limit into self.resources if needed."""
    limit = self._GetFlag('limit')
    if limit is None or limit < 0:
      return
    tap = display_taps.Limiter(limit)
    self._resources = peek_iterable.Tapper(self._resources, tap)

  def _AddPageTap(self):
    """Taps a resource pager into self.resources if needed."""
    page_size = self._GetFlag('page_size')
    if page_size is None or page_size <= 0:
      return
    tap = display_taps.Pager(page_size)
    self._resources = peek_iterable.Tapper(self._resources, tap)

  def _AddUriReplaceTap(self):
    """Taps a resource Uri replacer into self.resources if needed."""

    if not self._GetFlag('uri'):
      return

    tap = display_taps.UriReplacer(self._transform_uri)
    self._resources = peek_iterable.Tapper(self._resources, tap)

  def _GetResourceInfoDefaults(self):
    """Returns the default symbols for --filter and --format."""
    if not self._info:
      return self._defaults
    symbols = self._info.GetTransforms()
    if not symbols and not self._info.defaults:
      return self._defaults
    return resource_projection_spec.ProjectionSpec(
        defaults=resource_projection_spec.CombineDefaults(
            [self._info.defaults, self._defaults]),
        symbols=symbols)

  def _GetExplicitFormat(self):
    """Determines the explicit format.

    Returns:
      format: The format string, '' if there is no explicit format, or None
    """
    return self._args.format or ''

  def _GetDefaultFormat(self):
    """Determines the default format.

    Returns:
      format: The format string, '' if there is an explicit Display().
    """
    if hasattr(self._command, 'Display'):
      return ''
    return self._format

  def _GetFilter(self):
    flag_filter = self._GetFlag('filter')
    if flag_filter is None:
      if self._filter:
        log.info('Display filter: "%s"', six.text_type(self._filter))
      return self._filter
    else:
      return flag_filter

  def _GetFlatten(self):
    flag_flatten = self._GetFlag('flatten')
    if flag_flatten is None:
      return self._flatten
    else:
      return flag_flatten

  def GetFormat(self):
    """Determines the display format.

    Returns:
      format: The display format string.
    """
    default_fmt = self._GetDefaultFormat()
    fmt = self._GetExplicitFormat()

    if not fmt:
      # No explicit format.
      if self._GetFlag('uri'):
        return 'value(.)'
      # Use the default format.
      self._default_format_used = True
      fmt = default_fmt
    elif default_fmt:
      # Compose the default and explicit formats.
      #
      # The rightmost format in fmt takes precedence. Appending gives higher
      # precendence to the explicit format over the default format. Appending
      # also makes projection attributes from preceding projections available
      # to subsequent projections. For example, a user specified explicit
      # --format expression can use the column heading names instead of resource
      # key names:
      #
      #   table(foo.bar:label=NICE, state:STATUS) table(NICE, STATUS)
      #
      # or a --filter='s:DONE' expression can use alias named defined by the
      # defaults:
      #
      #   table(foo.bar:alias=b, state:alias=s)
      #
      fmt = default_fmt + ' ' + fmt

    if not fmt:
      return fmt
    sort_keys = self._GetSortKeys()
    if not sort_keys:
      return fmt

    # :(...) adds key only attributes that don't affect the projection.
    orders = []
    for order, (key, reverse) in enumerate(sort_keys, start=1):
      attr = ':reverse' if reverse else ''
      orders.append('{name}:sort={order}{attr}'.format(
          name=resource_lex.GetKeyName(key), order=order, attr=attr))
    fmt += ':({orders})'.format(orders=','.join(orders))
    return fmt

  def _InitPrinter(self):
    """Initializes the printer and associated attributes."""

    if self._printer_is_initialized:
      return
    self._printer_is_initialized = True

    # Determine the format.
    self._format = self.GetFormat()

    # Initialize the default symbols.
    self._defaults = self._GetResourceInfoDefaults()

    # Instantiate a printer if output is enabled.
    if self._format:
      self._printer = resource_printer.Printer(
          self._format, defaults=self._defaults, out=log.out)
      if self._printer:
        self._defaults = self._printer.column_attributes

  def GetReferencedKeyNames(self):
    """Returns the set of key names referenced by the command."""
    self._InitPrinter()
    return resource_reference.GetReferencedKeyNames(
        filter_string=self._GetFilter(),
        printer=self._printer,
        defaults=self._defaults)

  def _AddDisplayTaps(self):
    """Adds each of the standard display taps, if needed.

       The taps must be included in this order in order to generate the correct
       results. For example, limiting should not happen until after filtering is
       complete, and pagination should only happen on the fully trimmed results.
    """
    self._AddUriCacheTap()
    self._AddFlattenTap()
    self._AddFilterTap()
    self._AddSortByTap()
    self._AddLimitTap()
    self._AddPageTap()
    self._AddUriReplaceTap()

  def Display(self):
    """The default display method."""

    if not log.IsUserOutputEnabled():
      log.info('Display disabled.')
      # NOTICE: Do not consume resources here. Some commands use this case to
      # access the results of Run() via the return value of Execute(). However,
      # to satisfy callers who are only interetsted in silent side effects,
      # generators/iterators must be converted to a list here.
      if resource_property.IsListLike(self._resources):
        return list(self._resources)
      return self._resources

    # Initialize the printer.
    self._InitPrinter()

    self._AddDisplayTaps()

    resources_were_displayed = True
    if self._printer:
      # Most command output will end up here.
      log.info('Display format: "%s"', self._format)
      self._printer.Print(self._resources)
      resources_were_displayed = self._printer.ResourcesWerePrinted()
    elif hasattr(self._command, 'Display'):
      # This will eventually be rare.
      log.info('Explicit Display.')
      self._command.Display(self._args, self._resources)

    # Resource display is done.
    log.out.flush()

    # If the default format was used then display the epilog.
    if not self._args.IsSpecified('format'):
      self._command.Epilog(resources_were_displayed)

    return self._resources
