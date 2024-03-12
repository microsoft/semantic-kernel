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
"""Command for creating organization firewall policy associations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import firewall_policies_utils
from googlecloudsdk.command_lib.compute.firewall_policies import flags
from googlecloudsdk.core import log
import six


class Create(base.CreateCommand):
  """Create a new association between a firewall policy and an organization or folder resource.

  *{command}* is used to create organization firewall policy associations. An
  organization firewall policy is a set of rules that controls access to various
  resources.
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArgsCreateAssociation(parser)
    parser.display_info.AddCacheUpdater(flags.FirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    org_firewall_policy = client.OrgFirewallPolicy(
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())

    name = None
    attachment_target = None
    replace_existing_association = False

    if args.IsSpecified('name'):
      name = args.name

    attachment_target = None
    if args.IsSpecified('folder'):
      attachment_target = 'folders/' + args.folder
      if name is None:
        name = 'folder-' + args.folder

    if args.IsSpecified('organization') and attachment_target is None:
      attachment_target = 'organizations/' + args.organization
      if name is None:
        name = 'organization-' + args.organization

    if attachment_target is None:
      log.error(
          'Must specify attachment target with --organization=ORGANIZATION or '
          '--folder=FOLDER')
      sys.exit()

    replace_existing_association = False
    if args.replace_association_on_target:
      replace_existing_association = True

    association = holder.client.messages.FirewallPolicyAssociation(
        attachmentTarget=attachment_target, name=name)

    firewall_policy_id = firewall_policies_utils.GetFirewallPolicyId(
        org_firewall_policy,
        args.firewall_policy,
        organization=args.organization)
    return org_firewall_policy.AddAssociation(
        association=association,
        firewall_policy_id=firewall_policy_id,
        replace_existing_association=replace_existing_association,
        only_generate_request=False)


Create.detailed_help = {
    'EXAMPLES':
        """\
    To associate an organization firewall policy under folder with ID
    ``123456789" to folder ``987654321", run:

      $ {command} --firewall-policy=123456789 --folder=987654321
    """,
}
