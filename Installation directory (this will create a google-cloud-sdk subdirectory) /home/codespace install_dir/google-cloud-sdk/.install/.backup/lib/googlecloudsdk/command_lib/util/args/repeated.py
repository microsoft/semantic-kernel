# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Utilities for updating primitive repeated args.

This code:

    from googlecloudsdk.command_lib.util import repeated

    class UpdateFoo(base.UpdateCommand)

      @staticmethod
      def Args(parser):
        # add "foo" resource arg
        repeated.AddPrimitiveArgs(
            parser, 'foo', 'baz-bars', 'baz bars',
            additional_help='The baz bars allow you to do a thing.')

      def Run(self, args):
        client = foos_api.Client()
        foo_ref = args.CONCEPTS.foo.Parse()
        foo_result = repeated.CachedResult.FromFunc(client.Get, foo_ref)
        new_baz_bars = repeated.ParsePrimitiveArgs(
            args, 'baz_bars', foo_result.GetAttrThunk('bazBars'))

        if new_baz_bars is not None:
          pass  # code to update the baz_bars


Makes a command that works like so:

    $ cli-tool foos update --set-baz-bars qux,quux
    [...]
    $ cli-tool foos update --help
    [...]
    These flags modify the member baz bars of this foo. The baz bars allow you
    to do a thing. At most one of these can be specified:

      --add-baz-bars=[BAZ_BAR,...]
         Append the given values to the current baz bars.

      --clear-baz-bars
         Empty the current baz bars.

      --remove-baz-bars=[BAZ_BAR,...]
         Remove the given values from the current baz bars.

      --set-baz-bars=[BAZ_BAR,...]
         Completely replace the current access levels with the given values.
    [...]

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import functools

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

from six.moves import map  # pylint: disable=redefined-builtin


class CachedResult(object):
  """Memoizer for a function call."""

  def __init__(self, thunk):
    self.thunk = thunk
    self._result = None

  @classmethod
  def FromFunc(cls, func, *args, **kwargs):
    return cls(functools.partial(func, *args, **kwargs))

  def Get(self):
    """Get the result of the function call (cached)."""
    if self._result is None:
      self._result = self.thunk()
    return self._result

  def GetAttrThunk(self, attr, transform=None):
    """Returns a thunk that gets the given attribute of the result of Get().

    Examples:

      >>> class A(object):
      ...   b = [1, 2, 3]
      >>> CachedResult([A()].pop).GetAttrThunk('b')()
      [1, 2, 3]
      >>> CachedResult([A()].pop).GetAttrThunk('b', lambda x: x+1)
      [2, 3, 4]

    Args:
      attr: str, the name of the attribute. Attribute should be iterable.
      transform: func, one-arg function that, if given, will be applied to
        every member of the attribute (which must be iterable) before returning
        it.

    Returns:
      zero-arg function which, when called, returns the attribute (possibly
        transformed) of the result (which is cached).
    """
    if transform:
      return lambda: list(map(transform, getattr(self.Get(), attr)))
    else:
      return lambda: getattr(self.Get(), attr)


def ParseResourceNameArgs(args, arg_name, current_value_thunk, resource_parser):
  """Parse the modification to the given repeated resource name field.

  To be used in combination with AddPrimitiveArgs. This variant assumes the
  repeated field contains resource names and will use the given resource_parser
  to convert the arguments to relative names.

  Args:
    args: argparse.Namespace of parsed arguments
    arg_name: string, the (plural) suffix of the argument (snake_case).
    current_value_thunk: zero-arg function that returns the current value of the
      attribute to be updated. Will be called lazily if required.
    resource_parser: one-arg function that returns a resource reference that
      corresponds to the resource name list to be updated.

  Raises:
    ValueError: if more than one arg is set.

  Returns:
    List of str: the new value for the field, or None if no change is required.
  """
  underscored_name = arg_name.replace('-', '_')
  remove = _ConvertValuesToRelativeNames(
      getattr(args, 'remove_' + underscored_name), resource_parser)
  add = _ConvertValuesToRelativeNames(
      getattr(args, 'add_' + underscored_name), resource_parser)
  clear = getattr(args, 'clear_' + underscored_name)
  # 'set' is allowed to be None, as it is deprecated.
  set_ = _ConvertValuesToRelativeNames(
      getattr(args, 'set_' + underscored_name, None), resource_parser)

  return _ModifyCurrentValue(remove, add, clear, set_, current_value_thunk)


def _ConvertValuesToRelativeNames(names, resource_parser):
  if names:
    names = [resource_parser(name).RelativeName() for name in names]
  return names


def ParsePrimitiveArgs(args, arg_name, current_value_thunk):
  """Parse the modification to the given repeated field.

  To be used in combination with AddPrimitiveArgs; see module docstring.

  Args:
    args: argparse.Namespace of parsed arguments
    arg_name: string, the (plural) suffix of the argument (snake_case).
    current_value_thunk: zero-arg function that returns the current value of the
      attribute to be updated. Will be called lazily if required.

  Raises:
    ValueError: if more than one arg is set.

  Returns:
    List of str: the new value for the field, or None if no change is required.

  """
  underscored_name = arg_name.replace('-', '_')
  remove = getattr(args, 'remove_' + underscored_name)
  add = getattr(args, 'add_' + underscored_name)
  clear = getattr(args, 'clear_' + underscored_name)
  set_ = getattr(args, 'set_' + underscored_name, None)

  return _ModifyCurrentValue(remove, add, clear, set_, current_value_thunk)


def _ModifyCurrentValue(remove, add, clear, set_, current_value_thunk):
  """Performs the modification of the current value based on the args.

  Args:
    remove: list[str], items to be removed from the current value.
    add: list[str], items to be added to the current value.
    clear: bool, whether or not to clear the current value.
    set_: list[str], items to replace the current value.
    current_value_thunk: zero-arg function that returns the current value of the
      attribute to be updated. Will be called lazily if required.

  Raises:
    ValueError: if more than one arg is set.

  Returns:
    List of str: the new value for the field, or None if no change is required.
  """
  if sum(map(bool, (remove, add, clear, set_))) > 1:
    raise ValueError('At most one arg can be set.')

  if remove is not None:
    current_value = current_value_thunk()
    new_value = [x for x in current_value if x not in remove]
  elif add is not None:
    current_value = current_value_thunk()
    new_value = current_value + [x for x in add if x not in current_value]
  elif clear:
    return []
  elif set_ is not None:
    return set_
  else:
    return None

  if new_value != current_value:
    return new_value
  else:
    return None


def AddPrimitiveArgs(parser,
                     resource_name,
                     arg_name,
                     property_name,
                     additional_help='',
                     metavar=None,
                     is_dict_args=False,
                     auto_group_help=True,
                     include_set=True):
  """Add arguments for updating a field to the given parser.

  Adds `--{add,remove,set,clear-<resource>` arguments.

  Args:
    parser: calliope.parser_extensions.ArgumentInterceptor, the parser to add
      arguments to.
    resource_name: str, the (singular) name of the resource being modified (in
      whatever format you'd like it to appear in help text).
    arg_name: str, the (plural) argument suffix to use (hyphen-case).
    property_name: str, the description of the property being modified (plural;
      in whatever format you'd like it to appear in help text)
    additional_help: str, additional help text describing the property.
    metavar: str, the name of the metavar to use (if different from
      arg_name.upper()).
    is_dict_args: boolean, True when the primitive args are dict args.
    auto_group_help: bool, True to generate a summary help.
    include_set: bool, True to include the (deprecated) set argument.
  """
  properties_name = property_name
  if auto_group_help:
    group_help = 'These flags modify the member {} of this {}.'.format(
        properties_name, resource_name)
    if additional_help:
      group_help += ' ' + additional_help
  else:
    group_help = additional_help
  group = parser.add_mutually_exclusive_group(group_help)
  metavar = metavar or arg_name.upper()
  args = [
      _GetAppendArg(arg_name, metavar, properties_name, is_dict_args),
      _GetRemoveArg(arg_name, metavar, properties_name, is_dict_args),
      _GetClearArg(arg_name, properties_name),
  ]
  if include_set:
    args.append(_GetSetArg(arg_name, metavar, properties_name, is_dict_args))
  for arg in args:
    arg.AddToParser(group)


def _GetAppendArg(arg_name, metavar, prop_name, is_dict_args):
  list_name = '--add-{}'.format(arg_name)
  list_help = 'Append the given values to the current {}.'.format(prop_name)
  dict_name = '--update-{}'.format(arg_name)
  dict_help = 'Update the given key-value pairs in the current {}.'.format(
      prop_name)
  return base.Argument(
      dict_name if is_dict_args else list_name,
      type=_GetArgType(is_dict_args),
      metavar=metavar,
      help=_GetArgHelp(dict_help, list_help, is_dict_args))


def _GetRemoveArg(arg_name, metavar, prop_name, is_dict_args):
  list_help = 'Remove the given values from the current {}.'.format(prop_name)
  dict_help = ('Remove the key-value pairs from the current {} with the given '
               'keys.').format(prop_name)
  return base.Argument(
      '--remove-{}'.format(arg_name),
      metavar=metavar,
      type=_GetArgType(is_dict_args),
      help=_GetArgHelp(dict_help, list_help, is_dict_args))


def _GetSetArg(arg_name, metavar, prop_name, is_dict_args):
  list_help = 'Completely replace the current {} with the given values.'.format(
      prop_name)
  dict_help = ('Completely replace the current {} with the given key-value '
               'pairs.').format(prop_name)
  return base.Argument(
      '--set-{}'.format(arg_name),
      type=_GetArgType(is_dict_args),
      metavar=metavar,
      help=_GetArgHelp(dict_help, list_help, is_dict_args))


def _GetClearArg(arg_name, prop_name):
  return base.Argument(
      '--clear-{}'.format(arg_name),
      action='store_true',
      help='Empty the current {}.'.format(prop_name))


def _GetArgType(is_dict_args):
  return arg_parsers.ArgDict() if is_dict_args else arg_parsers.ArgList()


def _GetArgHelp(dict_help, list_help, is_dict_args):
  return dict_help if is_dict_args else list_help
