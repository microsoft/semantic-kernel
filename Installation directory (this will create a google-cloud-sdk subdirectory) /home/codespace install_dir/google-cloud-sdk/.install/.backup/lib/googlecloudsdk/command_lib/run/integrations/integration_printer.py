# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Job-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import Optional

from frozendict import frozendict
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.command_lib.run.integrations import deployment_states
from googlecloudsdk.command_lib.run.integrations.formatters import base
from googlecloudsdk.command_lib.run.integrations.formatters import custom_domains_formatter
from googlecloudsdk.command_lib.run.integrations.formatters import default_formatter
from googlecloudsdk.command_lib.run.integrations.formatters import states
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages as runapps


INTEGRATION_PRINTER_FORMAT = 'integration'

_DEFAULT_FORMATTER = default_formatter.DefaultFormatter()
_INTEGRATION_FORMATTER_MAPS = frozendict({
    'custom-domains': custom_domains_formatter.CustomDomainsFormatter(),
})


class IntegrationPrinter(cp.CustomPrinterBase):
  """Prints the run Integration in a custom human-readable format."""

  def Transform(self, record: base.Record) -> cp._Marker:
    """Transform an integration into the output structure of marker classes."""
    formatter = GetFormatter(record.metadata)
    config_block = formatter.TransformConfig(record)
    component_block = (
        formatter.TransformComponentStatus(record)
        if record.status.resourceComponentStatuses
        else 'Status not available')

    lines = [
        self.Header(record),
        ' ',
        self._DeploymentProgress(record.latest_deployment,
                                 formatter),
        config_block,
        ' ',
        cp.Labeled([
            cp.Lines([
                'Integration Components',
                component_block
            ])
        ]),
    ]

    call_to_action = formatter.CallToAction(record)
    if call_to_action:
      lines.append(' ')
      lines.append(call_to_action)

    return cp.Lines(lines)

  def Header(self, record: base.Record):
    """Print the header of the integration.

    Args:
      record: dict, the integration.

    Returns:
      The printed output.
    """
    con = console_attr.GetConsoleAttr()
    formatter = GetFormatter(record.metadata)
    resource_state = states.UNKNOWN
    if record.status and record.status.state:
      resource_state = str(record.status.state)
    symbol = formatter.StatusSymbolAndColor(resource_state)
    return con.Emphasize(
        '{} Integration status: {} in region {}'.format(
            symbol, record.name, record.region
        )
    )

  def _DeploymentProgress(
      self,
      deployment: runapps.Deployment,
      formatter: base.BaseFormatter,
  ) -> str:
    """Returns a message denoting the deployment progress.

    If there is no ongoing deployment and the deployment was successful, then
    this will be empty.

    Currently this only shows something if the latest deployment was a failure.
    In the future this will be updated to show more granular statuses as the
    deployment is ongoing.

    Args:
      deployment:  The deployment object
      formatter: The specific formatter used for the integration type.

    Returns:
      The message denoting the most recent deployment's progress (failure).
    """
    if deployment is None:
      return ''

    state = str(deployment.status.state)

    if state == deployment_states.FAILED:
      reason = deployment.status.errorMessage
      symbol = formatter.StatusSymbolAndColor(states.FAILED)
      return '{} Latest deployment: FAILED - {}\n'.format(symbol, reason)

    return ''


def GetFormatter(
    metadata: Optional[types_utils.TypeMetadata] = None,
) -> base.BaseFormatter:
  """Returns the formatter for the given integration type.

  Args:
    metadata: the typekit metadata for the integration.

  Returns:
    A formatter object.
  """
  if not metadata: return _DEFAULT_FORMATTER
  return _INTEGRATION_FORMATTER_MAPS.get(metadata.integration_type,
                                         _DEFAULT_FORMATTER)
