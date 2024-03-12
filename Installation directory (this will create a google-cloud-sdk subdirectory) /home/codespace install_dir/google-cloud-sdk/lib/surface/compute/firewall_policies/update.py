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
"""Command for updating organization firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import firewall_policies_utils
from googlecloudsdk.command_lib.compute.firewall_policies import flags
import six


class Update(base.UpdateCommand):
  """Update a Compute Engine organization firewall policy.

  *{command}* is used to update organization firewall policies. An organization
  firewall policy is a set of rules that controls access to various resources.
  """

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_POLICY_ARG = flags.FirewallPolicyArgument(
        required=True, operation='update')
    cls.FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='update')
    flags.AddArgsUpdateFirewallPolicy(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)
    org_firewall_policy = client.OrgFirewallPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())
    fp_id = firewall_policies_utils.GetFirewallPolicyId(
        org_firewall_policy, ref.Name(), organization=args.organization)
    existing_firewall_policy = org_firewall_policy.Describe(
        fp_id=fp_id, only_generate_request=False)[0]
    firewall_policy = holder.client.messages.FirewallPolicy(
        description=args.description,
        fingerprint=existing_firewall_policy.fingerprint)

    return org_firewall_policy.Update(
        fp_id=fp_id,
        only_generate_request=False,
        firewall_policy=firewall_policy)


Update.detailed_help = {
    'EXAMPLES':
        """\
    To update an organization firewall policy with ID ``123456789" to change the
    description to ``New description", run:

      $ {command} 123456789 --description='New description'
    """,
}
