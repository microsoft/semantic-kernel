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

"""The Cloud SDK completion cache.

A completion cache is a persistent cache that stores the current list of names
for resources visible to the caller.  The cache generates lists of resources
that match prefixes and/or patterns, suitable for command line completers. The
name representation is resource specific.  See core.resource.resource_style for
details.

Refer to the resource_cache module for a detailed description of resource
parsing and representation.

    +---------------------------+
    | completion cache          |
    | +-----------------------+ |
    | | completer             | |
    | +-----------------------+ |
    |           ...             |
    +---------------------------+

A completion cache is implemented as an extended ResourceCache object that
contains Completer objects.  A Completer object:

* has a Complete() method that returns resource strings matching a pattern
* has methods to convert between strings and parameter tuples
* has an underlying ResourceCache Collection object that holds parameter tuples
* derives from resource_cache.Updater to update the collection parameter tuples

This module is resource agnostic.  All resource specific information is
encapsulated in resource specific Completer objects.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.core.cache import resource_cache

import six


@six.add_metaclass(abc.ABCMeta)
class Completer(resource_cache.Updater):
  """A completion cache resource string completer.

  Along with the Complete() method, a completer has two main functions, each
  handled by a mixin:
  (1) Convert between resource string and parameter tuple representations.
  (2) Retrieve the current list of resources for the collection. See
      resource_cache.Updater for details.
  """

  @abc.abstractmethod
  def StringToRow(self, string):
    """Returns the row representation of string.

    May fill in some column values

    Args:
      string: The resource string representation.

    Returns:
      The row representation of string.
    """
    pass

  def RowToTemplate(self, row):
    """Returns the row template of row for the Resource.Complete method.

    By default all parameters are treated as prefixes.

    Args:
      row: The resource parameter tuple.

    Returns:
      The row template of row for the Resource.Complete method.
    """
    row_template = list(row)
    if len(row) < self.columns:
      row_template += [''] * (self.columns - len(row))
    return [c if '*' in c else c + '*' for c in row_template]

  @abc.abstractmethod
  def RowToString(self, row, parameter_info=None):
    """Returns the string representation of row.

    Args:
      row: The resource parameter tuple.
      parameter_info: A ParamaterInfo object for accessing parameter values in
        the program state.

    Returns:
      The string representation of row.
    """
    pass

  def Complete(self, prefix, parameter_info):
    """Returns the list of strings matching prefix.

    Args:
      prefix: The resource prefix string to match.
      parameter_info: A ParamaterInfo object for accessing parameter values in
        the program state.

    Returns:
      The list of strings matching prefix.
    """
    row = self.StringToRow(prefix)
    row_template = self.RowToTemplate(row)
    rows = self.Select(row_template, parameter_info)
    return [self.RowToString(row, parameter_info) for row in rows]
