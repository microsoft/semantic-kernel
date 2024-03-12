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
"""Parameter info lib for resource completers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.core import properties


class ResourceParameterInfo(parameter_info_lib.ParameterInfoByConvention):
  """Gets parameter info for resource arguments."""

  def __init__(self, resource_info, parsed_args, argument, **kwargs):
    """Initializes."""
    self.resource_info = resource_info
    super(ResourceParameterInfo, self).__init__(
        parsed_args,
        argument,
        **kwargs)

  def GetValue(self, parameter_name, check_properties=True):
    """Returns the program state value for parameter_name.

    Args:
      parameter_name: The parameter name.
      check_properties: bool, whether to check the properties (unused).

    Returns:
      The program state value for parameter_name.
    """
    del check_properties  # Unused.
    attribute_name = (
        self.resource_info.resource_spec.AttributeName(parameter_name))
    current = properties.VALUES.core.disable_prompts.GetBool()
    # TODO(b/73073941): Come up with a better way to temporarily disable
    # prompts. This prevents arbitrary fallthroughs with prompting from
    # being run during completion.
    properties.VALUES.core.disable_prompts.Set(True)
    try:
      return deps.Get(
          attribute_name,
          self.resource_info.BuildFullFallthroughsMap(),
          parsed_args=self.parsed_args) if attribute_name else None
    except deps.AttributeNotFoundError:
      return None
    finally:
      properties.VALUES.core.disable_prompts.Set(current)

  def _AttributeName(self, parameter_name):
    """Helper function to get the corresponding attribute for a parameter."""
    return self.resource_info.resource_spec.AttributeName(parameter_name)

  def GetDest(self, parameter_name, prefix=None):
    """Returns the argument parser dest name for parameter_name with prefix.

    Args:
      parameter_name: The resource parameter name.
      prefix: The prefix name for parameter_name if not None.

    Returns:
      The argument parser dest name for parameter_name.
    """
    del prefix  # Unused.
    attribute_name = self._AttributeName(parameter_name)
    flag_name = self.resource_info.attribute_to_args_map.get(attribute_name,
                                                             None)
    if not flag_name:
      return None
    return util.NamespaceFormat(flag_name)

  def GetFlag(self, parameter_name, parameter_value=None,
              check_properties=True, for_update=False):
    """Returns the command line flag for parameter.

    If the flag is already present in program values, returns None.
    If the user needs to specify it, returns a string in the form
    '--flag-name=value'. If the flag is boolean and True, returns '--flag-name'.

    Args:
      parameter_name: The parameter name.
      parameter_value: The parameter value if not None. Otherwise
        GetValue() is used to get the value.
      check_properties: Check property values if parsed_args don't help.
      for_update: Return flag for a cache update command.

    Returns:
      The command line flag  for the parameter, or None.
    """
    del for_update
    attribute_name = self._AttributeName(parameter_name)
    flag_name = self.resource_info.attribute_to_args_map.get(
        attribute_name, None)
    if not flag_name:
      # Project attributes are typically elided in favor of the global --project
      # flag. If the project flag is brought under the concept argument umbrella
      # this can be removed.
      if attribute_name == 'project':
        flag_name = '--project'
      else:
        return None
    program_value = self.GetValue(parameter_name)
    if parameter_value != program_value:
      if parameter_value is None:
        parameter_value = program_value
      if parameter_value:
        if parameter_value is True:
          return flag_name
        return '{name}={value}'.format(name=flag_name, value=parameter_value)
    return None
