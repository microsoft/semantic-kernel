# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Unified diff resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import difflib
import io

from googlecloudsdk.core.resource import resource_printer_base


class DiffPrinter(resource_printer_base.ResourcePrinter):
  """A printer for a unified diff of the first two projection columns.

  A unified diff of the first two projection columns.

  Printer attributes:
    format: The format of the diffed resources. Each resource is converted
      to this format and the diff of the converted resources is displayed.
      The default is 'flattened'.
  """

  def __init__(self, *args, **kwargs):
    super(DiffPrinter, self).__init__(*args, by_columns=True,
                                      non_empty_projection_required=True,
                                      **kwargs)
    self._print_format = self.attributes.get('format', 'flattened')

  def _Diff(self, old, new):
    """Prints the unified diff of formatter output for old and new.

    Prints a unified diff, eg,
    ---

    +++

    @@ -27,6 +27,6 @@

     settings.pricingPlan:                             PER_USE
     settings.replicationType:                         SYNCHRONOUS
     settings.settingsVersion:                         1
    -settings.tier:                                    D1
    +settings.tier:                                    D0
     state:                                            RUNNABLE

    Args:
      old: The old original resource.
      new: The new changed resource.
    """
    # Fill a buffer with the object as rendered originally.
    buf_old = io.StringIO()
    printer = self.Printer(self._print_format, out=buf_old)
    printer.PrintSingleRecord(old)
    # Fill a buffer with the object as rendered after the change.
    buf_new = io.StringIO()
    printer = self.Printer(self._print_format, out=buf_new)
    printer.PrintSingleRecord(new)
    # Send these two buffers to the unified_diff() function for printing.
    lines_old = buf_old.getvalue().split('\n')
    lines_new = buf_new.getvalue().split('\n')
    lines_diff = difflib.unified_diff(lines_old, lines_new)
    for line in lines_diff:
      self._out.Print(line)

  def _AddRecord(self, record, delimit=False):
    """Immediately prints the first two columns of record as a unified diff.

    Records with less than 2 colums are silently ignored.

    Args:
      record: A JSON-serializable object.
      delimit: Prints resource delimiters if True.
    """
    title = self.attributes.get('title')
    if title:
      self._out.Print(title)
      self._title = None
    if len(record) > 1:
      self._Diff(record[0], record[1])
