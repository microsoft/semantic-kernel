# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Object representation format resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer_base

import six


class ObjectPrinter(resource_printer_base.ResourcePrinter):
  """Prints the object representation of each item in a list.

  Bypasses JSON-serialization and prints the object representation of each
  resource.

  Printer attributes:
    separator: The line printed between resources.
    terminator: The line printed after each resource.
  """

  def __init__(self, *args, **kwargs):
    super(ObjectPrinter, self).__init__(*args, by_columns=True, **kwargs)
    self._first_record = True
    self._separator = self.attributes.get('separator')
    self._terminator = self.attributes.get('terminator')
    self._process_record = lambda x: x  # Bypass projection and serialization.

  def _AddRecord(self, record, delimit=False):
    """Immediately prints the given record using the object representation.

    Args:
      record: An object.
      delimit: Display the separator.
    """
    if self._first_record:
      self._first_record = False
    elif delimit and self._separator is not None:
      self._out.Print(self._separator)
    self._out.write(six.text_type(record))
    if self._terminator is not None:
      self._out.Print(self._terminator)
