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

"""Cloud resource filter and format key reference utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_keys_expr
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_printer


def GetReferencedKeyNames(
    filter_string=None, format_string=None, printer=None, defaults=None):
  """Returns the set of key names referenced by filter / format expressions.

  NOTICE: OnePlatform is forgiving on filter and format key reference name
  spelling.  Use resource_property.GetMatchingIndex() when verifying against
  resource dictionaries to handle camel and snake case spellings.

  Args:
    filter_string: The resource filter expression string.
    format_string: The resource format expression string.
    printer: The parsed format_string.
    defaults: The resource format and filter default projection.

  Raises:
    ValueError: If both format_string and printer are specified.

  Returns:
    The set of key names referenced by filter / format expressions.
  """
  keys = set()

  # Add the format key references.
  if printer:
    if format_string:
      raise ValueError('Cannot specify both format_string and printer.')
  elif format_string:
    printer = resource_printer.Printer(format_string, defaults=defaults)
    defaults = printer.column_attributes
  if printer:
    for col in printer.column_attributes.Columns():
      keys.add(resource_lex.GetKeyName(col.key, omit_indices=True))

  # Add the filter key references.
  if filter_string:
    expr = resource_filter.Compile(
        filter_string, defaults=defaults, backend=resource_keys_expr.Backend())
    for key in expr.Evaluate(None):
      keys.add(resource_lex.GetKeyName(key, omit_indices=True))

  return keys
