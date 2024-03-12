# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for listing the rules of organization security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute.org_security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.org_security_policies import flags
from googlecloudsdk.command_lib.compute.org_security_policies import org_security_policies_utils
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
    match.config.srcIpRanges.list():label=SRC_RANGES,
    match.config.destIpRanges.list():label=DEST_RANGES,
    match.config.layer4Configs.map().org_firewall_rule().list():label=PORT_RANGES
  )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListRules(base.DescribeCommand, base.ListCommand):
  """List the rules of a Compute Engine organization security policy.

  *{command}* is used to list the rules of an organization security policy.
  """

  ORG_SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ORG_SECURITY_POLICY_ARG = flags.OrgSecurityPolicyArgument(
        required=True, operation='list rules for')
    cls.ORG_SECURITY_POLICY_ARG.AddArgument(parser, operation_type='get')
    parser.add_argument(
        '--organization',
        help=('Organization which the organization security policy belongs to. '
              'Must be set if SECURITY_POLICY is display name.'))
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.ORG_SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)
    org_security_policy = client.OrgSecurityPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())
    sp_id = org_security_policies_utils.GetSecurityPolicyId(
        org_security_policy, ref.Name(), organization=args.organization)
    response = org_security_policy.Describe(
        sp_id=sp_id, only_generate_request=False)
    if not response:
      return None
    return firewalls_utils.SortOrgFirewallRules(holder.client,
                                                response[0].rules)

  def Epilog(self, resources_were_displayed):
    del resources_were_displayed
    log.status.Print('\n' + LIST_NOTICE)


ListRules.detailed_help = {
    'EXAMPLES':
        """\
    To list the rules of an organization security policy with ID
    ``123456789", run:

      $ {command} list-rules 123456789

    To list all the fields of the rules of an organization security policy with
    ID ``123456789", run:

      $ {command} list-rules 123456789 --format="table(
        priority,
        action,
        direction,
        match.config.srcIpRanges.list():label=SRC_RANGES,
        match.config.destIpRanges.list():label=DEST_RANGES,
        match.config.layer4Configs.map().org_firewall_rule().list():label=PORT_RANGES,
        targetServiceAccounts.list():label=TARGET_SVC_ACCT,
        targetResources:label=TARGET_RESOURCES,
        ruleTupleCount,
        enableLogging,
        description)"
        """,
}
