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
"""Command for listing the rules of organization firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import firewall_policies_utils
from googlecloudsdk.command_lib.compute.firewall_policies import flags
from googlecloudsdk.core import log
import six

LIST_NOTICE = """\
To show all fields of the firewall, please show in JSON format: --format=json
To show more fields in table format, please see the examples in --help.
"""

DEFAULT_LIST_FORMAT = """\
  table(
    priority,
    direction,
    action,
    match.srcIpRanges.list():label=SRC_RANGES,
    match.destIpRanges.list():label=DEST_RANGES,
    match.layer4Configs.map().org_firewall_rule().list():label=PORT_RANGES
  )"""


class ListRules(base.DescribeCommand, base.ListCommand):
  """List the rules of a Compute Engine organization firewall policy.

  *{command}* is used to list the rules of an organization firewall policy.
  """

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_POLICY_ARG = flags.FirewallPolicyArgument(
        required=True, operation='list rules for')
    cls.FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='get')
    parser.add_argument(
        '--organization',
        help=('Organization which the organization firewall policy belongs to. '
              'Must be set if FIREWALL_POLICY is short name.'))
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)

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
    response = org_firewall_policy.Describe(
        fp_id=fp_id, only_generate_request=False)
    if not response:
      return None
    return firewalls_utils.SortFirewallPolicyRules(holder.client,
                                                   response[0].rules)

  def Epilog(self, resources_were_displayed):
    del resources_were_displayed
    log.status.Print('\n' + LIST_NOTICE)


ListRules.detailed_help = {
    'EXAMPLES':
        """\
    To list the rules of an organization firewall policy with ID
    ``123456789", run:

      $ {command} 123456789

    To list all the fields of the rules of an organization firewall policy with
    ID ``123456789", run:

      $ {command} 123456789 --format="table(
        priority,
        action,
        direction,
        match.srcIpRanges.list():label=SRC_RANGES,
        match.destIpRanges.list():label=DEST_RANGES,
        match.layer4Configs.map().org_firewall_rule().list():label=PORT_RANGES,
        targetServiceAccounts.list():label=TARGET_SVC_ACCT,
        targetResources:label=TARGET_RESOURCES,
        ruleTupleCount,
        enableLogging,
        description)"
        """,
}
