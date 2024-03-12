# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for deleting organization firewall policy associations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import firewall_policies_utils
from googlecloudsdk.command_lib.compute.firewall_policies import flags
import six


class Delete(base.DeleteCommand):
  """Delete a Compute Engine organization firewall policy association.

  *{command}* is used to delete organization firewall policy association.
  """

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_POLICY_ARG = flags.FirewallPolicyAssociationsArgument(
        required=True)
    cls.FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='delete')
    flags.AddArgsDeleteAssociation(parser)
    parser.display_info.AddCacheUpdater(flags.FirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)
    org_firewall_policy = client.OrgFirewallPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())
    firewall_policy_id = firewall_policies_utils.GetFirewallPolicyId(
        org_firewall_policy,
        args.firewall_policy,
        organization=args.organization)
    return org_firewall_policy.DeleteAssociation(
        firewall_policy_id=firewall_policy_id, only_generate_request=False)


Delete.detailed_help = {
    'EXAMPLES':
        """\
    To delete an association with name ``example-association" of an organization
    firewall policy with ID ``123456789", run:

      $ {command} example-association --firewall-policy=123456789
    """,
}
