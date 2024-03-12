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

"""list format resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.util import encoding
import six


def _HasDefaultRepr(obj):
  """Returns True if obj has default __repr__ and __str__ methods."""
  try:
    d = obj.__class__.__dict__
    return '__str__' not in d and '__repr__' not in d
  except AttributeError:
    return False


class ListPrinter(resource_printer_base.ResourcePrinter):
  """Prints the list representations of a JSON-serializable list.

  An ordered list of items.

  Printer attributes:
    always-display-title: Display the title even if there are no records.
    compact: Display all items in a record on one line.
  """

  def __init__(self, *args, **kwargs):
    super(ListPrinter, self).__init__(*args, by_columns=True, **kwargs)
    self._process_record_orig = self._process_record
    self._process_record = self._ProcessRecord
    self._separator = ' ' if 'compact' in self.attributes else '\n   '
    title = self.attributes.get('title', None)
    if title and 'always-display-title' in self.attributes:
      self._out.write(title + '\n')
      title = None
    self._title = title

  def _ProcessRecord(self, record):
    """Applies process_record_orig to dict, list and default repr records.

    Args:
      record: A JSON-serializable object.

    Returns:
      The processed record.
    """
    if isinstance(record, (dict, list)) or _HasDefaultRepr(record):
      record = self._process_record_orig(record)
    if isinstance(record, dict):
      return ['{0}: {1}'.format(k, v) for k, v in sorted(six.iteritems(record))
              if v is not None]
    if isinstance(record, list):
      return [i for i in record if i is not None]
    return [encoding.Decode(record or '')]

  def _AddRecord(self, record, delimit=False):
    """Immediately prints the given record as a list item.

    Args:
      record: A JSON-serializable object.
      delimit: Prints resource delimiters if True.
    """
    if self._title:
      self._out.write(self._title + '\n')
      self._title = None
    self._out.write(' - ' + self._separator.join(
        map(six.text_type, self.RemoveHiddenColumns(record))) + '\n')
