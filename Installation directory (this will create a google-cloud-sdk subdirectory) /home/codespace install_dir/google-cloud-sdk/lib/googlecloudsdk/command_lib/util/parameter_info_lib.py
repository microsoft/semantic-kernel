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

"""Calliope parsed resource parameter info objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.core import properties
from googlecloudsdk.core.cache import resource_cache
from googlecloudsdk.core.resource import resource_property


def GetDestFromParam(param, prefix=None):
  """Returns a conventional dest name given param name with optional prefix."""
  name = param.replace('-', '_').strip('_')
  if prefix:
    name = prefix + '_' + name
  return resource_property.ConvertToSnakeCase(
      re.sub('s?I[Dd]$', '', name)).strip('_')


def GetFlagFromDest(dest):
  """Returns a conventional flag name given a dest name."""
  return '--' + dest.replace('_', '-')


def GetDestFromFlag(flag):
  """Returns a conventional dest name given a flag name."""
  return flag.replace('-', '_').strip('_')


class ParameterInfoByConvention(resource_cache.ParameterInfo):
  """An object for accessing parameter values in the program state.

  "program state" is defined by this class.  It could include parsed command
  line arguments and properties.  The class can also map between resource and
  program parameter names.

  This ParameterInfo object provides default methods based on resource
  argument naming conventions. It should be used as a fallback only. The
  ResourceArgument object should derive a ParameterInfo that provides the
  exact parameter/argument information. It can do this in the ParameterInfo
  method of the completer object.

  The naming conventions are:

    - A parsed resource parameter name, with trailing s?I[Dd] deleted, and
      converted to snake_case is also the command line flag or positional parsed
      args Namespace dest name.
    - Argument specific flag names use the dest as a prefix, for example,
      if dest is 'foo', then the zone flag is either --foo-zone or --zone.
    - Property values are in the property section named by the collection API
      (the first dotted component of the collection name) and/or the core
      section, checked in that order.  For example, for the 'compute.instances'
      collection the API is 'compute' and the zone property is 'compute/zone',
      and the 'project' property is 'compute/project' or 'core/project'.

  Attributes:
    _api: The collection API name.
    _argument: The argument object that the completer for this parameter info
      is attached to.
    _parsed_args: The parsed command line args Namespace.
    _prefix: The related flag prefix.
  """

  def __init__(self, parsed_args, argument, collection=None, **kwargs):
    super(ParameterInfoByConvention, self).__init__(**kwargs)
    self._parsed_args = parsed_args
    self._argument = argument
    self._prefix = argument.dest if argument else None
    self._api = collection.split('.')[0] if collection else None

  @property
  def argument(self):
    return self._argument

  @property
  def parsed_args(self):
    return self._parsed_args

  def _GetFlagAndDest(self, dest):
    """Returns the argument parser (flag_name, flag_dest) for dest.

    Args:
      dest: The resource argument dest name.

    Returns:
      Returns the argument parser (flag_name, flag_dest) for dest.
    """
    dests = []
    if self._prefix:
      dests.append(self.GetDest(dest, prefix=self._prefix))
    dests.append(dest)
    for flag_dest in dests:
      try:
        return self._parsed_args.GetFlag(flag_dest), flag_dest
      except parser_errors.UnknownDestinationException:
        pass
    return None, None

  def _GetPropertyValue(self, dest):
    """Returns the property value for dest.

    Args:
      dest: The resource argument dest.

    Returns:
      The property value for dest.
    """
    props = []
    if self._api:
      props.append(self._api + '/' + dest)
    props.append(dest)
    for prop in props:
      try:
        return properties.FromString(prop).Get()
      except properties.NoSuchPropertyError:
        pass
    return None

  def GetDest(self, parameter_name, prefix=None):
    """Returns the argument parser dest name for parameter_name with prefix.

    Args:
      parameter_name: The resource parameter name.
      prefix: The prefix name for parameter_name if not None.

    Returns:
      The argument parser dest name for parameter_name.
    """
    return GetDestFromParam(parameter_name, prefix=prefix)

  def GetFlag(self, parameter_name, parameter_value=None,
              check_properties=True, for_update=False):
    """Returns the command line flag for parameter[=parameter_value].

    Args:
      parameter_name: The parameter name.
      parameter_value: The parameter value if not None. Otherwise
        GetValue() is used to get the value.
      check_properties: Check property values if parsed_args don't help.
      for_update: Return flag for a cache update command.

    Returns:
      The command line flag the for parameter.
    """
    del for_update
    dest = self.GetDest(parameter_name)
    flag, flag_dest = self._GetFlagAndDest(dest)
    if not flag:
      # Try the plural form to handle sub-resources.
      dest += 's'
      flag, flag_dest = self._GetFlagAndDest(dest)
      if not flag:
        return None
    program_value = self._parsed_args.GetValue(flag_dest)
    if program_value is None and check_properties:
      program_value = self._GetPropertyValue(dest)
    if parameter_value != program_value:
      if parameter_value is None:
        parameter_value = program_value
      if parameter_value:
        if parameter_value is True:
          return flag
        return '{name}={value}'.format(name=flag, value=parameter_value)
    return None

  def GetValue(self, parameter_name, check_properties=True):
    """Returns the program state value for parameter_name.

    Args:
      parameter_name: The parameter name.
      check_properties: Check property values if parsed_args don't help.

    Returns:
      The program state value for parameter_name.
    """
    value = None
    dest = self.GetDest(parameter_name)
    for name in [self.GetDest(parameter_name, prefix=self._prefix), dest]:
      try:
        value = self._parsed_args.GetValue(name)
        break
      except parser_errors.UnknownDestinationException:
        pass
    if value is None and check_properties:
      value = self._GetPropertyValue(dest)
    return value

  def Execute(self, command, call_arg_complete=False):
    """Executes command in the current CLI.

    Args:
      command: The command arg list to execute.
      call_arg_complete: Enable arg completion if True.

    Returns:
      Returns the list of resources from the command.
    """
    call_arg_complete = False
    # pylint: disable=protected-access
    return self._parsed_args._Execute(
        command, call_arg_complete=call_arg_complete)
