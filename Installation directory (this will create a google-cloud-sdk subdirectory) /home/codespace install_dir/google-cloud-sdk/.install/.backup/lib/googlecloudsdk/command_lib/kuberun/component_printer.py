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
"""KubeRun Component printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.core.resource import resource_property

COMPONENT_PRINTER_FORMAT = 'component'


class ComponentPrinter(cp.CustomPrinterBase):
  """Prints the KubeRun Component custom human-readable format."""

  def Transform(self, record):
    """Transform a service into the output structure of marker classes."""
    sections = [
        self._Header(record),
        self._SpecSection(record),
    ] + self._ConfigSections(record)
    return cp.Lines(_Spaced(sections))

  def _Header(self, record):
    con = console_attr.GetConsoleAttr()
    return con.Emphasize('Component {}'.format(record['metadata']['name']))

  def _SpecSection(self, record):
    spec = record.get('spec', {})
    return cp.Section([cp.Labeled([
        ('Type', spec.get('type', '')),
        ('DevKit', spec.get('devkit', '')),
        ('DevKit Version', spec.get('devkit-version', '')),
    ])])

  def _ConfigSections(self, record):
    config = record.get('spec', {}).get('config', {})
    sections = []
    for section_name, data in sorted(config.items()):
      title = _ConfigTitle(section_name)
      section = cp.Section([
          cp.Labeled([(title, _ConfigSectionData(data))])
      ])
      sections.append(section)
    return sections


def _ConfigTitle(section_name):
  return resource_property.ConvertToSnakeCase(section_name).replace(
      '_', ' ').replace('-', ' ').title()


def _Spaced(lines):
  """Adds a line of space between the passed in lines."""
  spaced_lines = []
  for line in lines:
    if spaced_lines:
      spaced_lines.append(' ')
    spaced_lines.append(line)
  return spaced_lines


def _ConfigSectionData(data):
  if isinstance(data, list):
    # These items are rendered with a line of space between them because
    # otherwise it is hard to tell that the items are distinct.
    return cp.Lines(_Spaced([_ConfigItem(item) for item in data]))
  return _ConfigItem(data)


def _ConfigItem(data):
  if isinstance(data, dict):
    return cp.Labeled([
        (key, _ConfigItem(value)) for key, value in sorted(data.items())
    ])
  return data
