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
"""Utilities for updating primitive dict args."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import yaml


def MapUpdateFlag(
    flag_name,
    long_name,
    key_type,
    value_type,
    key_metavar='KEY',
    value_metavar='VALUE',
):
  return base.Argument(
      '--update-{}'.format(flag_name),
      metavar='{}={}'.format(key_metavar, value_metavar),
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(key_type=key_type, value_type=value_type),
      help='List of key-value pairs to set as {}.'.format(long_name),
  )


def AddMapUpdateFlag(
    group,
    flag_name,
    long_name,
    key_type,
    value_type,
    key_metavar='KEY',
    value_metavar='VALUE',
):
  return MapUpdateFlag(
      flag_name,
      long_name,
      key_type,
      value_type,
      key_metavar=key_metavar,
      value_metavar=value_metavar,
  ).AddToParser(group)


def MapRemoveFlag(flag_name, long_name, key_type, key_metavar='KEY'):
  return base.Argument(
      '--remove-{}'.format(flag_name),
      metavar=key_metavar,
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgList(element_type=key_type),
      help='List of {} to be removed.'.format(long_name),
  )


def AddMapRemoveFlag(group, flag_name, long_name, key_type, key_metavar='KEY'):
  return MapRemoveFlag(
      flag_name, long_name, key_type, key_metavar=key_metavar
  ).AddToParser(group)


def MapClearFlag(flag_name, long_name):
  return base.Argument(
      '--clear-{}'.format(flag_name),
      action='store_true',
      help='Remove all {}.'.format(long_name),
  )


def AddMapClearFlag(group, flag_name, long_name):
  return MapClearFlag(flag_name, long_name).AddToParser(group)


def MapSetFlag(
    flag_name,
    long_name,
    key_type,
    value_type,
    key_metavar='KEY',
    value_metavar='VALUE',
):
  return base.Argument(
      '--set-{}'.format(flag_name),
      metavar='{}={}'.format(key_metavar, value_metavar),
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(key_type=key_type, value_type=value_type),
      help=(
          'List of key-value pairs to set as {0}. All existing {0} will be '
          'removed first.'
      ).format(long_name),
  )


def AddMapSetFlag(
    group,
    flag_name,
    long_name,
    key_type,
    value_type,
    key_metavar='KEY',
    value_metavar='VALUE',
):
  return MapSetFlag(
      flag_name,
      long_name,
      key_type,
      value_type,
      key_metavar=key_metavar,
      value_metavar=value_metavar,
  ).AddToParser(group)


class ArgDictFile(object):
  """Interpret a YAML file as a dict."""

  def __init__(self, key_type=None, value_type=None):
    """Initialize an ArgDictFile.

    Args:
      key_type: (str)->str, A function to apply to each of the dict keys.
      value_type: (str)->str, A function to apply to each of the dict values.
    """
    self.key_type = key_type
    self.value_type = value_type

  def __call__(self, file_path):
    map_file_dict = yaml.load_path(file_path)
    map_dict = {}
    if not yaml.dict_like(map_file_dict):
      raise arg_parsers.ArgumentTypeError(
          'Invalid YAML/JSON data in [{}], expected map-like data.'.format(
              file_path
          )
      )
    for key, value in map_file_dict.items():
      if self.key_type:
        try:
          key = self.key_type(key)
        except ValueError:
          raise arg_parsers.ArgumentTypeError('Invalid key [{0}]'.format(key))
      if self.value_type:
        try:
          value = self.value_type(value)
        except ValueError:
          raise arg_parsers.ArgumentTypeError(
              'Invalid value [{0}]'.format(value)
          )
      map_dict[key] = value
    return map_dict


def AddMapSetFileFlag(group, flag_name, long_name, key_type, value_type):
  group.add_argument(
      '--{}-file'.format(flag_name),
      metavar='FILE_PATH',
      type=ArgDictFile(key_type=key_type, value_type=value_type),
      help=(
          'Path to a local YAML file with definitions for all {0}. All '
          'existing {0} will be removed before the new {0} are added.'
      ).format(long_name),
  )


def AddUpdateMapFlags(
    parser, flag_name, long_name=None, key_type=None, value_type=None
):
  """Add flags for updating values of a map-of-atomic-values property.

  Args:
    parser: The argument parser
    flag_name: The name for the property to be used in flag names
    long_name: The name for the property to be used in help text
    key_type: A function to apply to map keys.
    value_type: A function to apply to map values.
  """
  if not long_name:
    long_name = flag_name

  group = parser.add_mutually_exclusive_group()
  update_remove_group = group.add_argument_group(
      help=(
          'Only --update-{0} and --remove-{0} can be used together.  If both '
          'are specified, --remove-{0} will be applied first.'
      ).format(flag_name)
  )
  AddMapUpdateFlag(
      update_remove_group,
      flag_name,
      long_name,
      key_type=key_type,
      value_type=value_type,
  )
  AddMapRemoveFlag(update_remove_group, flag_name, long_name, key_type=key_type)
  AddMapClearFlag(group, flag_name, long_name)
  AddMapSetFlag(
      group, flag_name, long_name, key_type=key_type, value_type=value_type
  )
  AddMapSetFileFlag(
      group, flag_name, long_name, key_type=key_type, value_type=value_type
  )


def GetMapFlagsFromArgs(flag_name, args):
  """Get the flags for updating this map and return their values in a dict.

  Args:
    flag_name: The base name of the flags
    args: The argparse namespace

  Returns:
    A dict of the flag values
  """
  specified_args = args.GetSpecifiedArgs()
  return {
      'set_flag_value': specified_args.get('--set-{}'.format(flag_name)),
      'update_flag_value': specified_args.get('--update-{}'.format(flag_name)),
      'clear_flag_value': specified_args.get('--clear-{}'.format(flag_name)),
      'remove_flag_value': specified_args.get('--remove-{}'.format(flag_name)),
      'file_flag_value': specified_args.get('--{}-file'.format(flag_name)),
  }


def ApplyMapFlags(
    old_map,
    set_flag_value,
    update_flag_value,
    clear_flag_value,
    remove_flag_value,
    file_flag_value,
):
  """Determine the new map property from an existing map and parsed arguments.

  Args:
    old_map: the existing map
    set_flag_value: The value from the --set-* flag
    update_flag_value: The value from the --update-* flag
    clear_flag_value: The value from the --clear-* flag
    remove_flag_value: The value from the --remove-* flag
    file_flag_value: The value from the --*-file flag

  Returns:
    A new map with the changes applied.
  """

  if clear_flag_value:
    return {}
  if set_flag_value:
    return set_flag_value
  if file_flag_value:
    return file_flag_value
  if update_flag_value or remove_flag_value:
    old_map = old_map or {}
    remove_flag_value = remove_flag_value or []
    new_map = {k: v for k, v in old_map.items() if k not in remove_flag_value}
    new_map.update(update_flag_value or {})
    return new_map
  return old_map
