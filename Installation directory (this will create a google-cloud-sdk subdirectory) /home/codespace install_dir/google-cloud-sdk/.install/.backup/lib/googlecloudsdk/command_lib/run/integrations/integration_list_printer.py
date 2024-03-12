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
"""Represents the rows of the the 'gcloud run integrations list' command.

The client.ListIntegrations output is formatted into the Row class listed below,
which allows for formatted output to the console.  The list command registers
a table that references the field names in the Row class.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run.integrations import deployment_states
from googlecloudsdk.command_lib.run.integrations.formatters import base


class Row(object):
  """Represents the fields that will be used in the output of the table.

  Having a single class that has the expected values here is better than passing
  around a dict as the keys could mispelled or changed in one place.
  """

  def __init__(self, integration_name, integration_type,
               services, latest_deployment_status, region: str):
    self.integration_name = integration_name
    self.integration_type = integration_type
    self.services = services
    self.latest_deployment_status = latest_deployment_status
    self.region = region
    self.formatted_latest_deployment_status = (
        _GetSymbolFromDeploymentStatus(latest_deployment_status)
    )

  def __eq__(self, other):
    return (self.integration_name == other.integration_name and
            self.integration_type == other.integration_type and
            self.services == other.services and
            self.latest_deployment_status == other.latest_deployment_status and
            self.region == other.region
           )


def _GetSymbolFromDeploymentStatus(status):
  """Gets a symbol based on the latest deployment status.

  If a deployment cannot be found or the deployment is not in a 'SUCCEEDED',
  'FAILED', or 'IN_PROGRESS' state, then it should be reported as 'FAILED'.

  This would be true for integrations where the deployment never kicked off
  due to a failure.

  Args:
    status: The latest deployment status.

  Returns:
    str, the symbol to be placed in front of the integration name.
  """
  status_to_symbol = {
      deployment_states.SUCCEEDED:
          base.GetSymbol(base.SUCCESS),
      deployment_states.FAILED:
          base.GetSymbol(base.FAILED),
      deployment_states.IN_PROGRESS:
          base.GetSymbol(base.UPDATING),
  }

  return status_to_symbol.get(status,
                              base.GetSymbol(
                                  base.FAILED
                                  )
                              )
