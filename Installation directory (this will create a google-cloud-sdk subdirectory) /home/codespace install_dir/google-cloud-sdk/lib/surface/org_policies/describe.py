# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Describe command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Describes an organization policy.
      """,
    'EXAMPLES':
        """\
      To describe the policy associated with the constraint 'gcp.resourceLocations'
      and the Project 'foo-project', run:

      $ {command} gcp.resourceLocations --project=foo-project
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an organization policy."""

  @staticmethod
  def Args(parser):
    arguments.AddConstraintArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--effective',
        action='store_true',
        help='Describe the effective policy.')

  def Run(self, args):
    """Gets the (effective) organization policy.

    If --effective is not specified, then the policy is retrieved using
    GetPolicy.

    If --effective is specified, then the effective policy is retrieved using
    GetEffectivePolicy.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       The retrieved policy.
    """
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    policy_name = utils.GetPolicyNameFromArgs(args)

    if args.effective:
      return org_policy_api.GetEffectivePolicy(policy_name)

    return org_policy_api.GetPolicy(policy_name)


Describe.detailed_help = DETAILED_HELP
