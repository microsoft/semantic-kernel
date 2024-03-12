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
"""List command for the Org Policy CLI."""

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
      Lists the policies set on a resource.
      """,
    'EXAMPLES':
        """\
      To list the policies set on the Project 'foo-project', run:

      $ {command} --project=foo-project
      """,
}


def HasListPolicy(spec):
  if not spec:
    return False
  for rule in spec.rules:
    if (rule.values is not None or rule.allowAll is not None or
        rule.denyAll is not None):
      return True
  return False


def HasDryRunListPolicy(dry_run_spec):
  if not dry_run_spec:
    return False
  for rule in dry_run_spec.rules:
    if (rule.values is not None or rule.allowAll is not None or
        rule.denyAll is not None):
      return True
  return False


def HasBooleanPolicy(spec):
  if spec:
    return any([rule.enforce is not None for rule in spec.rules])
  return False


def HasDryRunBooleanPolicy(dry_run_spec):
  if dry_run_spec:
    return any([rule.enforce is not None for rule in dry_run_spec.rules])
  return False


def PolicyOutput(is_policy_set, is_dry_run_policy_set):
  if is_policy_set and is_dry_run_policy_set:
    return 'LIVE_AND_DRY_RUN_SET'
  elif is_policy_set:
    return 'SET'
  elif is_dry_run_policy_set:
    return 'DRY_RUN_SET'
  return '-'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the policies set on a resource."""

  @staticmethod
  def Args(parser):
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--show-unset',
        action='store_true',
        help='Show all available constraints for the resource.')

    parser.display_info.AddFormat(
        'table(constraint, listPolicy, booleanPolicy, etag)')

  def Run(self, args):
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    parent = utils.GetResourceFromArgs(args)
    output = []

    policies = org_policy_api.ListPolicies(parent).policies
    for policy in policies:
      spec = policy.spec
      dry_run_spec = policy.dryRunSpec
      list_policy_set = HasListPolicy(spec)
      boolean_policy_set = HasBooleanPolicy(spec)
      dry_run_boolean_policy_set = HasDryRunBooleanPolicy(dry_run_spec)
      dry_run_list_policy_set = HasDryRunListPolicy(dry_run_spec)
      boolean_policy_output = PolicyOutput(boolean_policy_set,
                                           dry_run_boolean_policy_set)
      list_policy_output = PolicyOutput(list_policy_set,
                                        dry_run_list_policy_set)
      output.append({
          'constraint': policy.name.split('/')[-1],
          'listPolicy': list_policy_output,
          'booleanPolicy': boolean_policy_output,
          'etag': policy.etag,
      })
    if args.show_unset:
      constraints = org_policy_api.ListConstraints(parent).constraints

      existing_policy_names = {row['constraint'] for row in output}
      for constraint in constraints:
        constraint_name = constraint.name.split('/')[-1]
        if constraint_name not in existing_policy_names:
          output.append({
              'constraint': constraint_name,
              'listPolicy': '-',
              'booleanPolicy': '-'
          })

    return output


List.detailed_help = DETAILED_HELP
