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

"""Resource printer base class.

Each printer has three main attributes, all accessible as strings in the
--format='NAME[ATTRIBUTES](PROJECTION)' option:

  NAME: str, The printer name.

  [ATTRIBUTES]: str, An optional [no-]name[=value] list of attributes. Unknown
    attributes are silently ignored. Attributes are added to a printer local
    dict indexed by name.

  (PROJECTION): str, List of resource names to be included in the output
    resource. Unknown names are silently ignored. Resource names are
    '.'-separated key identifiers with an implicit top level resource name.

Example:

  gcloud compute instances list \
      --format='table[box](name, networkInterfaces[0].networkIP)'
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_property


# Structured output indentation.
STRUCTURED_INDENTATION = 2


class Error(core_exceptions.Error):
  """Exceptions for this module."""


class ProjectionRequiredError(Error):
  """Format missing required projection exception."""


class _ResourceMarker(object):
  """A marker that can be injected into resource lists."""

  def Act(self, printer):
    """Called by ResourcePrinter.Addrecord().

    Args:
      printer: The printer object.
    """
    pass


class FinishMarker(_ResourceMarker):
  """A resource list Finish marker."""

  def Act(self, printer):
    printer.Finish()


class PageMarker(_ResourceMarker):
  """A resource list Page marker."""

  def Act(self, printer):
    printer.Page()


def IsResourceMarker(resource):
  """Returns True if resource is a _ResourceMarker."""
  return isinstance(resource, _ResourceMarker)


class ResourcePrinter(object):
  """Base class for printing JSON-serializable Python objects.

  Attributes:
    attributes: Optional printer attribute dict indexed by attribute name.
    column_attributes: Projection column attributes.
    _console_attr: The console attributes. May be ignored by some printers.
    _empty: True if there are no records.
    _heading: The list of column heading label strings.
    _name: Format name.
    _non_empty_projection_required: True if the printer requires a non-empty
      projection.
    _out: Output stream.
    _process_record: The function called to process each record passed to
      AddRecord() before calling _AddRecord(). It is called like this:
        record = process_record(record)
    _printer: The resource_printer.Printer method for nested formats.
    _is_column_visible: List of Boolean values indicating if indexed column is
      visible
  """

  def __init__(self, out=None, name=None, projector=None, by_columns=False,
               ignore_default_transforms=False, process_record=None,
               non_empty_projection_required=False, printer=None,
               console_attr=None, retain_none_values=False):
    """Constructor.

    Args:
      out: The output stream, log.out if None. If the 'private' attribute is set
        and the output stream is a log._ConsoleWriter then the underlying stream
        is used instead to disable output to the log file.
      name: The format name.
      projector: Optional resource Projector.
      by_columns: True if AddRecord() expects a list of columns.
      ignore_default_transforms: Ignore default projection transforms if True.
      process_record: The function called to process each record passed to
        AddRecord() before calling _AddRecord(). It is called like this:
          record = process_record(record)
      non_empty_projection_required: True if the printer requires a non-empty
        projection.
      printer: The resource_printer.Printer method for nested formats.
      console_attr: The console attributes for the output stream. Ignored by
        some printers. If None then printers that require it will initialize it
        to match out.
      retain_none_values: Retain resurce dict entries with None values.
    """
    self._console_attr = console_attr
    self._empty = True
    self._heading = None
    self._name = name
    self._non_empty_projection_required = non_empty_projection_required
    self._out = out or log.out
    self._printer = printer
    self._pager = False
    self._pager_out = None

    if not projector:
      projector = resource_projector.Compile()
    self._process_record = process_record or projector.Evaluate
    projector.SetByColumns(by_columns)
    projector.SetIgnoreDefaultTransforms(ignore_default_transforms)
    projection = projector.Projection()
    if projection:
      self.attributes = projection.Attributes() or {}
      self.column_attributes = projection
      if 'debug' in self.attributes:
        log.status.Print('{0} format projection:'.format(projection.Name()))
        projection.Print(log.status)
    else:
      self.attributes = {}
      self.column_attributes = None
    if 'no-undefined' in self.attributes:
      retain_none_values = False
    projector.SetRetainNoneValues(retain_none_values)

    if 'private' in self.attributes:
      try:
        # Disable log file writes by printing directly to the console stream.
        self._out = self._out.GetConsoleWriterStream()
      except AttributeError:
        pass

    if 'pager' in self.attributes and out is None:
      self._pager_out = self._out
      self._out = io.StringIO()
      self._pager = True
    self._SetVisibleColumns()

  def _SetVisibleColumns(self):
    """Sets visible columns list if column attributes have been loaded."""
    if self.column_attributes:
      self._is_column_visible = [
          not column.attribute.hidden
          for column in self.column_attributes.Columns()
      ]
    else:
      self._is_column_visible = None

  def RemoveHiddenColumns(self, row):
    """Returns a list of visible columns given a row."""
    if not self._is_column_visible:
      self._SetVisibleColumns()
    if self._is_column_visible:
      return [col for i, col in enumerate(row) if self._is_column_visible[i]]
    else:
      return row

  def AddHeading(self, heading):
    """Overrides the default heading.

    If the printer does not support headings then this is a no-op.

    Args:
      heading: List of column heading strings that overrides the default
        heading.
    """
    self._heading = heading

  def _AddRecord(self, record, delimit=True):
    """Format specific AddRecord().

    Args:
      record: A JSON-serializable object.
      delimit: Prints resource delimiters if True.
    """
    pass

  def AddRecord(self, record, delimit=True):
    """Adds a record for printing.

    Streaming formats (e.g., YAML) can print results at each AddRecord() call.
    Non-streaming formats (e.g., JSON, table(...)) may cache data at each
    AddRecord() call and not print until Finish() is called.

    Args:
      record: A JSON-serializable object.
      delimit: Prints resource delimiters if True.
    """
    if IsResourceMarker(record):
      record.Act(self)
    else:
      self._empty = False
      self._AddRecord(self._process_record(record), delimit)

  def Finish(self):
    """Prints the results for non-streaming formats.

    Must be called via super if overridden.
    """
    if self._pager and self._out:
      try:
        console_io.More(self._out.getvalue(), out=self._pager_out)
      # Can happen if caller provided a different out that is not type StringIO.
      except AttributeError:
        pass

  def ResourcesWerePrinted(self):
    """Returns True if some resource items were printed or printer disabled."""
    return not self._empty

  def Page(self):
    """Flushes intermediate results for streaming formats."""
    pass

  def PrintSingleRecord(self, record):
    """Print one record by itself.

    Args:
      record: A JSON-serializable object.
    """
    self.AddRecord(record, delimit=False)
    self.Finish()

  def Print(self, resources, single=False, intermediate=False):
    """Prints resources using printer.AddRecord() and printer.Finish().

    Args:
      resources: A singleton or list of JSON-serializable Python objects.
      single: If True then resources is a single item and not a list.
        For example, use this to print a single object as JSON.
      intermediate: This is an intermediate call, do not call Finish().

    Raises:
      ProjectionRequiredError: If the projection is empty and the format
        requires a non-empty projection.
    """
    if 'disable' in self.attributes:
      # Disable formatted output and do not consume the resources.
      self._empty = False
      return
    if self._non_empty_projection_required and (
        not self.column_attributes or not self.column_attributes.Columns()):
      raise ProjectionRequiredError(
          'Format [{0}] requires a non-empty projection. Use key parameters to specify a projection like so `{0}(foo, bar.baz)`'
          .format(self._name))
    # Resources may be a generator and since generators can raise exceptions, we
    # have to call Finish() in the finally block to make sure that the resources
    # we've been able to pull out of the generator are printed before control is
    # given to the exception-handling code.
    try:
      if resources:
        if single or not resource_property.IsListLike(resources):
          self.AddRecord(resources, delimit=intermediate)
        else:
          for resource in resources:
            self.AddRecord(resource)
    finally:
      if not intermediate:
        self.Finish()

  def Printer(self, *args, **kwargs):
    """Calls the resource_printer.Printer() method (for nested printers)."""
    return self._printer(*args, **kwargs)
