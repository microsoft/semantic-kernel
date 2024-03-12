# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
import re

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.resource import yaml_printer


class ACMDiffPrinter(resource_printer_base.ResourcePrinter):
  """A printer for an ndiff of the first two projection columns.

  A unified diff of the first two projection columns.

  Printer attributes:
    format: The format of the diffed resources. Each resource is converted
      to this format and the diff of the converted resources is displayed.
      The default is 'yaml'.
  """

  def __init__(self, *args, **kwargs):
    super(ACMDiffPrinter, self).__init__(
        *args, by_columns=True, non_empty_projection_required=True, **kwargs)
    self._print_format = self.attributes.get('format', 'yaml')

  def _Diff(self, old, new):
    """Prints a modified ndiff of formatter output for old and new.

    IngressPolicies:
     ingressFrom:
       sources:
         accessLevel: accessPolicies/123456789/accessLevels/my_level
        -resource: projects/123456789012
        +resource: projects/234567890123
    EgressPolicies:
      +egressTo:
        +operations:
          +actions:
            +action: method_for_all
            +actionType: METHOD
          +serviceName: chemisttest.googleapis.com
        +resources:
          +projects/345678901234
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
    lines_old = ''
    lines_new = ''
    # Send these two buffers to the ndiff() function for printing.
    if old is not None:
      lines_old = self._FormatYamlPrinterLinesForDryRunDescribe(
          buf_old.getvalue().split('\n'))
    if new is not None:
      lines_new = self._FormatYamlPrinterLinesForDryRunDescribe(
          buf_new.getvalue().split('\n'))

    lines_diff = difflib.ndiff(lines_old, lines_new)

    empty_line_pattern = re.compile(r'^\s*$')
    empty_config_pattern = re.compile(r'^(\+|-)\s+\{\}$')
    for line in lines_diff:
      # We want to show the entire contents of resource, but without the
      # additional information added by ndiff, which always leads with '?'. We
      # also don't want to show empty lines produced from comparing unset
      # fields, as well as lines produced from comparing empty messages, which
      # will look like '+ {}' or '- {}'.
      if line and line[0] != '?' and not empty_line_pattern.match(
          line) and not empty_config_pattern.match(line):
        print(line)

  def _AddRecord(self, record, delimit=False):
    """Immediately prints the first two columns of record as a unified diff.

    Records with less than 2 columns are silently ignored.

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

  def _FormatYamlPrinterLinesForDryRunDescribe(self, lines):
    """Tweak yaml printer formatted resources for ACM's dry run describe output.

    Args:
      lines: yaml printer formatted strings

    Returns:
      lines with no '-' prefix for yaml array elements.
    """
    return [line.replace('-', ' ', 1) for line in lines]


class Error(exceptions.Error):
  """Exceptions for this module."""


class UnknownFormatError(Error):
  """Unknown format name exception."""


_FORMATTERS = {
    'default': yaml_printer.YamlPrinter,
    'diff': ACMDiffPrinter,
    'yaml': yaml_printer.YamlPrinter,
}


def Print(resources, print_format, out=None, defaults=None, single=False):
  """Prints the given resources.

  Args:
    resources: A singleton or list of JSON-serializable Python objects.
    print_format: The _FORMATTER name with optional projection expression.
    out: Output stream, log.out if None.
    defaults: Optional resource_projection_spec.ProjectionSpec defaults.
    single: If True then resources is a single item and not a list. For example,
      use this to print a single object as JSON.
  """
  printer = Printer(print_format, out=out, defaults=defaults)
  # None means the printer is disabled.
  if printer:
    printer.Print(resources, single)


def Printer(print_format, out=None, defaults=None, console_attr=None):
  """Returns a resource printer given a format string.

  Args:
    print_format: The _FORMATTERS name with optional attributes and projection.
    out: Output stream, log.out if None.
    defaults: Optional resource_projection_spec.ProjectionSpec defaults.
    console_attr: The console attributes for the output stream. Ignored by some
      printers. If None then printers that require it will initialize it to
      match out.

  Raises:
    UnknownFormatError: The print_format is invalid.

  Returns:
    An initialized ResourcePrinter class or None if printing is disabled.
  """
  projector = resource_projector.Compile(
      expression=print_format,
      defaults=resource_projection_spec.ProjectionSpec(
          defaults=defaults, symbols=resource_transform.GetTransforms()))
  printer_name = projector.Projection().Name()
  if not printer_name:
    # Do not print, do not consume resources.
    return None
  try:
    printer_class = _FORMATTERS[printer_name]
  except KeyError:
    raise UnknownFormatError("""\
  Format for acm_printer must be one of {0}; received [{1}].
  """.format(', '.join(SupportedFormats()), printer_name))

  printer = printer_class(
      out=out,
      name=printer_name,
      printer=Printer,
      projector=projector,
      console_attr=console_attr)
  return printer


def SupportedFormats():
  """Returns a sorted list of supported format names."""
  return sorted(_FORMATTERS)
