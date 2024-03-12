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
"""Command for deleting organization security policy rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import org_security_policy_rule_utils as rule_utils
from googlecloudsdk.api_lib.compute.org_security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.org_security_policies import flags
from googlecloudsdk.command_lib.compute.org_security_policies import org_security_policies_utils
import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a Compute Engine organization security policy rule.

  *{command}* is used to delete organization security policy rule.
  """

  ORG_SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ORG_SECURITY_POLICY_ARG = flags.OrgSecurityPolicyRuleArgument(
        required=True, operation="delete")
    cls.ORG_SECURITY_POLICY_ARG.AddArgument(parser)
    flags.AddSecurityPolicyId(parser, operation="deleted")
    flags.AddOrganization(parser, required=False)
    parser.display_info.AddCacheUpdater(flags.OrgSecurityPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.ORG_SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)
    security_policy_rule_client = client.OrgSecurityPolicyRule(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())
    security_policy_id = org_security_policies_utils.GetSecurityPolicyId(
        security_policy_rule_client,
        args.security_policy,
        organization=args.organization)
    return security_policy_rule_client.Delete(
        priority=rule_utils.ConvertPriorityToInt(ref.Name()),
        security_policy_id=security_policy_id,
        only_generate_request=False)


Delete.detailed_help = {
    "EXAMPLES":
        """\
    To delete a rule with priority ``10" in an organization security policy with
    ID ``123456789", run:

      $ {command} delete 10 --security-policy=123456789
    """,
}
