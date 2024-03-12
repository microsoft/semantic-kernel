# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Default formatter for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import re
from typing import Any, Optional

from apitools.base.py import encoding
from googlecloudsdk.command_lib.run.integrations.formatters import base
from googlecloudsdk.command_lib.run.integrations.formatters import states
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.core.resource import yaml_printer as yp


class DefaultFormatter(base.BaseFormatter):
  """Format logics when no integration specific formatter is matched."""

  def TransformConfig(self, record: base.Record) -> cp._Marker:
    """Print the config of the integration.

    Args:
      record: integration_printer.Record class that just holds data.

    Returns:
      The printed output.
    """
    if record.metadata and record.metadata.parameters:
      labeled = []
      config_dict = (
          encoding.MessageToDict(record.resource.config)
          if record.resource.config
          else {}
      )
      for param in record.metadata.parameters:
        if config_dict.get(param.config_name):
          name = param.label if param.label else param.config_name
          labeled.append((name, config_dict.get(param.config_name)))
      return cp.Labeled(labeled)
    if record.resource.config:
      return cp.Lines([self._PrintAsYaml({'config': record.resource.config})])
    return None

  def TransformComponentStatus(self, record: base.Record) -> cp._Marker:
    """Print the component status of the integration.

    Args:
      record: dict, the integration.

    Returns:
      The printed output.
    """
    components = []
    comp_statuses = (
        record.status.resourceComponentStatuses if record.status else []
    )
    for r in comp_statuses:
      console_link = r.consoleLink if r.consoleLink else 'n/a'
      state_name = str(r.state).upper() if r.state else 'N/A'
      state_symbol = self.StatusSymbolAndColor(state_name)
      components.append(
          cp.Lines([
              '{} ({})'.format(self.PrintType(r.type), r.name),
              cp.Labeled([
                  ('Console link', console_link),
                  ('Resource Status', state_symbol + ' ' + state_name),
              ]),
          ])
      )
    return cp.Labeled(components)

  def CallToAction(self, record: base.Record) -> Optional[str]:
    """Call to action to use generated environment variables.

    If the resource state is not ACTIVE then the resource is not ready for
    use and the call to action will not be shown.

    It supports simple template value subsitution. Supported keys are:
    %%project%%: the name of the project
    %%region%%: the region
    %%config.X%%: the attribute from Resource's config with key 'X'
    %%status.X%%: the attribute from ResourceStatus' extraDetails with key 'X'

    Args:
      record: integration_printer.Record class that just holds data.

    Returns:
      A formatted string of the call to action message,
      or None if no call to action is required.
    """
    state = str(record.status.state)
    if state != states.ACTIVE or not record.metadata or not record.metadata.cta:
      return None

    message = record.metadata.cta
    variables = re.findall(r'%%([\w.]+)%%', message)
    for variable in variables:
      value = None
      if variable == 'project':
        value = properties.VALUES.core.project.Get(required=True)
      elif variable == 'region':
        value = record.region
      elif variable.startswith('config.'):
        if record.resource and record.resource.config:
          config_key = variable.replace('config.', '')
          res_config = encoding.MessageToDict(record.resource.config)
          value = res_config.get(config_key)
      elif variable.startswith('status.'):
        if record.status and record.status.extraDetails:
          details_key = variable.replace('status.', '')
          res_config = encoding.MessageToDict(record.status.extraDetails)
          value = res_config.get(details_key)

      if value is None:
        value = 'N/A'

      key = '%%{}%%'.format(variable)
      message = message.replace(key, value)

    return message

  def _PrintAsYaml(self, content: Any) -> str:
    buffer = io.StringIO()
    printer = yp.YamlPrinter(buffer)
    printer.Print(content)
    return buffer.getvalue()
