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
"""Command for creating organization firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import flags
import six


class Create(base.CreateCommand):
  """Create a Compute Engine organization firewall policy.

  *{command}* is used to create organization firewall policies. An organization
  firewall policy is a set of rules that controls access to various resources.
  """

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    flags.AddArgFirewallPolicyCreation(parser)
    parser.display_info.AddCacheUpdater(flags.FirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    org_firewall_policy = client.OrgFirewallPolicy(
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())

    if args.IsSpecified('organization'):
      parent_id = 'organizations/' + args.organization
    elif args.IsSpecified('folder'):
      parent_id = 'folders/' + args.folder
    firewall_policy = holder.client.messages.FirewallPolicy(
        description=args.description, displayName=args.short_name)
    return org_firewall_policy.Create(
        firewall_policy=firewall_policy,
        parent_id=parent_id,
        only_generate_request=False)


Create.detailed_help = {
    'EXAMPLES':
        """\
    To create an organization firewall policy under folder with ID ``123456789",
    run:

      $ {command} --short-name=my-policy --folder=123456789
    """,
}
