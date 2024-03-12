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
"""'vmware external-access-rules delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.externalaccessrules import ExternalAccessRulesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_policies import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a VMware Engine external access firewall rule.
        """,
    'EXAMPLES':
        """
          To delete an external access firewall rule called `my-external-access-rule` in project `my-project` and region `us-west2` associated with network policy `my-network-policy`, run:

            $ {command} my-external-access-rule --location=us-west2 --project=my-project --network-policy=my-network-policy

          Or:

            $ {command} my-external-access-rule --network-policy=my-network-policy

          In the second example, the project and the location are taken from gcloud properties core/project and compute/region respectively.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a VMware Engine external access rule."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddExternalAccessRuleToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    external_access_rule = args.CONCEPTS.external_access_rule.Parse()
    client = ExternalAccessRulesClient()
    is_async = args.async_
    operation = client.Delete(external_access_rule)
    if is_async:
      log.DeletedResource(
          operation.name,
          kind='VMware Engine external access rule',
          is_async=True)
      return operation

    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for external access rule [{}] to be deleted'.format(
            external_access_rule.RelativeName()),
        has_result=False)
