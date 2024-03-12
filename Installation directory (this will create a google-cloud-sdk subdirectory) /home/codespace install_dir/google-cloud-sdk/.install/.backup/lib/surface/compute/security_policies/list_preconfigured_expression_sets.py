# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to list all available preconfigured expression sets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class ListPreconfiguredExpressionSets(base.ListCommand):
  """List all available preconfigured expression sets.

  *{command}* lists all available preconfigured expression sets that can be used
  with the Cloud Armor rules language.

  ## EXAMPLES

  To list all current preconfigured expressions sets run this:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    """Set up arguments for this command."""
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        """
        table(id:label=EXPRESSION_SET,
              aliases:format="get([])",
              expressions:format="table(id:label=RULE_ID,
                                        sensitivity:label=SENSITIVITY)")
    """
    )

  def Run(self, args):
    """Issues the request to list available preconfigured expression sets."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    project = properties.VALUES.core.project.Get(required=True)
    request = (
        messages.ComputeSecurityPoliciesListPreconfiguredExpressionSetsRequest(
            project=project))
    response = client.securityPolicies.ListPreconfiguredExpressionSets(request)

    if response.preconfiguredExpressionSets is not None:
      return response.preconfiguredExpressionSets.wafRules.expressionSets
    return response.preconfiguredExpressionSets
