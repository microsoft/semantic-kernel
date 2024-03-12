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
"""Set-policy command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from argcomplete import completers
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Sets an organization policy from a JSON or YAML file. The policy will be
      created if it does not exist, or updated if it already exists.
      """,
    'EXAMPLES':
        """\
      Organization policy list constraint YAML file example:

        name: projects/PROJECT_ID/policies/CONSTRAINT_NAME
        spec:
          rules:
          - values:
            denied_values:
            - VALUE_A

      Organization policy list constraint JSON file example:

        {
          "name": "projects/PROJECT_ID/policies/CONSTRAINT_NAME",
          "spec": {
            "rules": [
              {
                "values": {
                    "deniedValues": ["VALUE_A"]
                }
              }
            ]
          }
        }

      To set the policy from the file on the path './sample_path', run:

        $ {command} ./sample_path
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetPolicy(base.Command):
  """Set an organization policy from a JSON or YAML file."""

  @staticmethod
  def Args(parser):
    arguments.AddUpdateMaskArgToParser(parser)
    parser.add_argument(
        'policy_file',
        metavar='POLICY_FILE',
        completer=completers.FilesCompleter,
        help='Path to JSON or YAML file that contains the organization policy.')

  def Run(self, args):
    """Creates or updates a policy from a JSON or YAML file.

    This first converts the contents of the specified file into a policy object.
    It then fetches the current policy using GetPolicy. If it does not exist,
    the policy is created using CreatePolicy. If it does, the retrieved policy
    is checked to see if it needs to be updated. If so, the policy is updated
    using UpdatePolicy.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The created or updated policy.
    """
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    input_policy = utils.GetMessageFromFile(args.policy_file,
                                            self.ReleaseTrack())
    update_mask = utils.GetUpdateMaskFromArgs(args)
    if not input_policy.name:
      raise exceptions.InvalidInputError(
          'Name field not present in the organization policy.')

    try:
      policy = org_policy_api.GetPolicy(input_policy.name)
    except api_exceptions.HttpNotFoundError:
      if update_mask:
        log.warning(
            'A policy for the input constraint does not exist on the '
            'resource and so the flag `--update-mask` will be ignored. '
            'The policy will be set as per input policy file.'
        )
      create_response = org_policy_api.CreatePolicy(input_policy)
      log.CreatedResource(input_policy.name, 'policy')
      return create_response

    if policy == input_policy:
      return policy

    update_response = org_policy_api.UpdatePolicy(input_policy, update_mask)
    log.UpdatedResource(input_policy.name, 'policy')
    return update_response


SetPolicy.detailed_help = DETAILED_HELP
