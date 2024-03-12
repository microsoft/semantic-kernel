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

"""config format resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import shlex

from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.util import platforms

import six


class ConfigPrinter(resource_printer_base.ResourcePrinter):
  """Prints a dictionary of dictionaries in config style.

  A dictionary of dictionaries in config style.

  Printer attributes:
    export: Display the dictionary as a list of system specific
      environment export commands.
    unset: Display the dictionary as a list of system specific
      environment unset commands.
  """

  def __init__(self, *args, **kwargs):
    super(ConfigPrinter, self).__init__(*args, retain_none_values=True,
                                        **kwargs)
    if 'export' in self.attributes:
      self._add_items = self._PrintEnvExport
      if platforms.OperatingSystem.IsWindows():
        self._env_command_format = 'set {name}={value}\n'
      else:
        self._env_command_format = 'export {name}={value}\n'
    elif 'unset' in self.attributes:
      self._add_items = self._PrintEnvUnset
      if platforms.OperatingSystem.IsWindows():
        self._env_command_format = 'set {name}=\n'
      else:
        self._env_command_format = 'unset {name}\n'
    else:
      self._add_items = self._PrintConfig
    # Print the title if specified.
    if 'title' in self.attributes:
      self._out.write(self.attributes['title'] + '\n')

  def _PrintCategory(self, out, label, items):
    """Prints config items in the label category.

    Args:
      out: The output stream for this category.
      label: A list of label strings.
      items: The items to list for label, either dict iteritems, an enumerated
        list, or a scalar value.
    """
    top = io.StringIO()
    sub = io.StringIO()
    for name, value in sorted(items):
      name = six.text_type(name)
      try:
        values = six.iteritems(value)
        self._PrintCategory(sub, label + [name], values)
        continue
      except AttributeError:
        pass
      if value is None:
        top.write('{name} (unset)\n'.format(name=name))
      elif isinstance(value, list):
        self._PrintCategory(sub, label + [name], enumerate(value))
      else:
        top.write('{name} = {value}\n'.format(name=name, value=value))
    top_content = top.getvalue()
    sub_content = sub.getvalue()
    if label and (top_content or
                  sub_content and not sub_content.startswith('[')):
      out.write('[{0}]\n'.format('.'.join(label)))
    if top_content:
      out.write(top_content)
    if sub_content:
      out.write(sub_content)

  def _PrintConfig(self, items):
    """Prints config items in the root category.

    Args:
      items: The current record dict iteritems from _AddRecord().
    """
    self._PrintCategory(self._out, [], items)

  @staticmethod
  def _Prefix(prefix, name):
    """Returns a new prefix based on prefix and name."""
    if isinstance(name, int):
      name = 'I' + six.text_type(name)
    return prefix + name + '_'

  def _PrintEnvExport(self, items, prefix=''):
    """Prints the environment export commands for items.

    Environment variable names have '_' instead of '.'.  Array values have
    subscripts expanded as names *_I0, *_I1, ...

    Args:
      items: The current record dict iteritems from _AddRecord().
      prefix: Parent name prefix, prepended to each item name.
    """
    for name, value in sorted(items):
      name = six.text_type(name)
      if isinstance(value, dict):
        self._PrintEnvExport(six.iteritems(value),
                             prefix=self._Prefix(prefix, name))
      elif value is None:
        self._out.write('{name} (unset)\n'.format(name=prefix + name))
      elif isinstance(value, list):
        for i, v in enumerate(value):
          if not isinstance(v, dict):
            v = {'I' + six.text_type(i): v}
          self._PrintEnvExport(six.iteritems(v),
                               prefix=self._Prefix(prefix, name))
      else:
        value = shlex.quote(six.text_type(value))
        self._out.write(self._env_command_format.format(
            name=prefix + name, value=value))

  def _PrintEnvUnset(self, items, prefix=''):
    """Prints the environment unset commands for items.

    Args:
      items: The current record dict iteritems from _AddRecord().
      prefix: Parent name prefix, prepended to each item name.
    """
    for name, value in sorted(items):
      name = six.text_type(name)
      if isinstance(value, dict):
        self._PrintEnvUnset(six.iteritems(value),
                            prefix=self._Prefix(prefix, name))
      elif isinstance(value, list):
        for i, v in enumerate(value):
          if not isinstance(v, dict):
            v = {'I' + six.text_type(i): v}
          self._PrintEnvUnset(six.iteritems(v),
                              prefix=self._Prefix(prefix, name))
      else:
        self._out.write(self._env_command_format.format(name=prefix + name))

  def _AddRecord(self, record, delimit=False):
    """Dispatches to the specific config printer.

    Nothing is printed if the record is not a JSON-serializable dict.

    Args:
      record: A JSON-serializable dict.
      delimit: Ignored.
    """
    try:
      self._add_items(six.iteritems(record))
    except AttributeError:
      pass
