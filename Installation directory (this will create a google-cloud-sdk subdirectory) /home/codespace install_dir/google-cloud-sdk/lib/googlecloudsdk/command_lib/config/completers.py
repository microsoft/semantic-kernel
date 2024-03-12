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

"""Argcomplete completers for various config related things."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import module_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs


def PropertiesCompleter(prefix, **unused_kwargs):
  """An argcomplete completer for property and section names."""
  all_sections = properties.VALUES.AllSections()
  options = []

  if '/' in prefix:
    # Section has been specified, only return properties under that section.
    parts = prefix.split('/', 1)
    section = parts[0]
    prefix = parts[1]
    if section in all_sections:
      section_str = section + '/'
      props = properties.VALUES.Section(section).AllProperties()
      options.extend([section_str + p for p in props if p.startswith(prefix)])
  else:
    # No section.  Return matching sections and properties in the default
    # group.
    options.extend([s + '/' for s in all_sections if s.startswith(prefix)])
    section = properties.VALUES.default_section.name
    props = properties.VALUES.Section(section).AllProperties()
    options.extend([p for p in props if p.startswith(prefix)])

  return options


def NamedConfigCompleter(prefix, **unused_kwargs):
  """An argcomplete completer for existing named configuration names."""
  configs = list(named_configs.ConfigurationStore.AllConfigs().keys())
  return [c for c in configs if c.startswith(prefix)]


class PropertyValueCompleter(completers.Converter):
  """A completer for a specific property value.

  The property value to be completed is not known until completion time.
  """

  def Complete(self, prefix, parameter_info):
    properties.VALUES.core.print_completion_tracebacks.Set(True)
    prop_name = parameter_info.GetValue('property')
    if not prop_name:
      # No property specified. This should have been caught by the caller.
      return None
    prop = properties.FromString(prop_name)
    if not prop:
      # Property is invalid. This should have been caught by the caller.
      return None

    if prop.choices:
      # Fixed set of possible values - easy.
      return [c for c in prop.choices if c.startswith(prefix)]

    if prop.completer:
      # prop.completer is the module path for the resource value completer.
      completer_class = module_util.ImportModule(prop.completer)
      completer = completer_class(cache=self.cache)
      return completer.Complete(prefix, parameter_info)

    # No completer for this property.
    return None

  def Update(self, parameter_info=None, aggregations=None):
    """No completion cache for properties."""
    del parameter_info, aggregations
