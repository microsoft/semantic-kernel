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
"""Set-custom-constraint command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from argcomplete import completers
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Sets a Custom Constraint from a JSON or YAML file. The custom
      constraint will be created if it does not exist, or updated if it
      already exists.
      """,
    'EXAMPLES':
        """\
      To set the custom constraint from the file on the path './sample_path', run:

        $ {command} ./sample_path
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetCustomConstraint(base.Command):
  """Set a custom constraint from a JSON or YAML file."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'custom_constraint_file',
        metavar='CUSTOM_CONSTRAINT_FILE',
        completer=completers.FilesCompleter,
        help='Path to JSON or YAML file that contains the organization policy.')

  def Run(self, args):
    """Creates or updates a custom constraint from a JSON or YAML file.

    This first converts the contents of the specified file into a custom
    constraint object. It then fetches the current custom constraint using
    GetCustomConstraint. If it does not exist, the custom constraint is created
    using CreateCustomConstraint. If it does, the retrieved custom constraint is
    checked to see if it needs to be updated. If so, the custom constraint is
    updated using UpdateCustomConstraint.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The created or updated custom constraint.
    """
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    input_custom_constraint = utils.GetCustomConstraintMessageFromFile(
        args.custom_constraint_file, self.ReleaseTrack())
    if not input_custom_constraint.name:
      raise exceptions.InvalidInputError(
          'Name field not present in the custom constraint.')
    if not input_custom_constraint.name.startswith('organizations/'):
      raise exceptions.InvalidInputError(
          'Name field contains invalid resource type: ' +
          input_custom_constraint.name +
          '. Custom constraints can be created only on organization resources.')
    try:
      custom_constraint = org_policy_api.GetCustomConstraint(
          input_custom_constraint.name)
    except api_exceptions.HttpNotFoundError:
      create_response = org_policy_api.CreateCustomConstraint(
          input_custom_constraint)
      log.CreatedResource(input_custom_constraint.name, 'custom constraint')
      return create_response
    if custom_constraint == input_custom_constraint:
      return custom_constraint
    update_response = org_policy_api.UpdateCustomConstraint(
        input_custom_constraint)
    log.UpdatedResource(input_custom_constraint.name, 'custom constraint')
    return update_response


SetCustomConstraint.detailed_help = DETAILED_HELP
