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
"""Command for creating organization security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.org_security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.org_security_policies import flags
import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a Compute Engine organization security policy.

  *{command}* is used to create organization security policies. An organization
  security policy is a set of rules that controls access to various resources.
  """

  ORG_SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    flags.AddArgSpCreation(parser)
    parser.display_info.AddCacheUpdater(flags.OrgSecurityPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    org_security_policy = client.OrgSecurityPolicy(
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())

    if args.IsSpecified('organization'):
      parent_id = 'organizations/' + args.organization
    elif args.IsSpecified('folder'):
      parent_id = 'folders/' + args.folder
    security_policy = holder.client.messages.SecurityPolicy(
        description=args.description,
        displayName=args.display_name,
        type=holder.client.messages.SecurityPolicy.TypeValueValuesEnum.FIREWALL)
    return org_security_policy.Create(
        security_policy=security_policy,
        parent_id=parent_id,
        only_generate_request=False)


Create.detailed_help = {
    'EXAMPLES':
        """\
    To create an organization security policy under folder with ID ``123456789",
    run:

      $ {command} create --folder=123456789
    """,
}
