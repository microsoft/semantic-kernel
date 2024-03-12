# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Delete-custom-constraint command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Deletes a custom constraint.
      """,
    'EXAMPLES':
        """\
      To delete the custom constraint 'custom.myCustomConstraint' associated
      with the Organization '1234', run:

      $ {command} custom.myCustomConstraint --organization=1234
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeleteCustomConstraint(base.DeleteCommand):
  """Deletes a custom constraint."""

  @staticmethod
  def Args(parser):
    arguments.AddCustomConstraintArgToParser(parser)
    arguments.AddOrganizationResourceFlagsToParser(parser)

  def Run(self, args):
    """Deletes the custom constraint.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       If the custom constraint is deleted, then messages.GoogleProtobufEmpty.
    """
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    custom_constraint_name = utils.GetCustomConstraintFromArgs(args)

    delete_response = org_policy_api.DeleteCustomConstraint(
        custom_constraint_name)
    log.DeletedResource(custom_constraint_name, 'custom constraint')
    return delete_response


DeleteCustomConstraint.detailed_help = DETAILED_HELP
