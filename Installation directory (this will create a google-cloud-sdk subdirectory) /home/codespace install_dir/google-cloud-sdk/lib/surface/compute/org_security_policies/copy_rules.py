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
"""Command for replace rules of organization security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.org_security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.org_security_policies import flags
from googlecloudsdk.command_lib.compute.org_security_policies import org_security_policies_utils
import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CopyRules(base.UpdateCommand):
  """Replace the rules of a Compute Engine organization security policy with rules from another policy.

  *{command}* is used to replace the rules of organization security policies. An
   organization security policy is a set of rules that controls access to
   various resources.
  """

  ORG_SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ORG_SECURITY_POLICY_ARG = flags.OrgSecurityPolicyArgument(
        required=True, operation='copy the rules to')
    cls.ORG_SECURITY_POLICY_ARG.AddArgument(parser, operation_type='copy-rules')
    flags.AddArgsCopyRules(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.ORG_SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)
    org_security_policy = client.OrgSecurityPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())
    dest_sp_id = org_security_policies_utils.GetSecurityPolicyId(
        org_security_policy, ref.Name(), organization=args.organization)
    return org_security_policy.CopyRules(
        only_generate_request=False,
        dest_sp_id=dest_sp_id,
        source_security_policy=args.source_security_policy)


CopyRules.detailed_help = {
    'EXAMPLES':
        """\
    To copy the rules of an organization security policy with ID ``123456789", from
    another organization security policy with ID ``987654321", run:

      $ {command} copy-rules 123456789 --source-security-policy=987654321
    """,
}
