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
"""Reset command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Resets the policy to the default for the constraint.
      """,
    'EXAMPLES':
        """\
      To reset the policy associated with the constraint 'gcp.resourceLocations' and
      the Project 'foo-project', run:

        $ {command} gcp.resourceLocations --project=foo-project
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Reset(base.Command):
  """Reset the policy to the default for the constraint."""

  @staticmethod
  def Args(parser):
    arguments.AddConstraintArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)
    arguments.AddUpdateMaskArgToParser(parser)

  def ShouldUpdateLiveSpec(self, update_mask):
    return (
        update_mask is None
        or update_mask == '*'
        or update_mask == 'policy.spec'
    )

  def ShouldUpdateDryRunSpec(self, update_mask):
    return update_mask == '*' or update_mask == 'policy.dry_run_spec'

  def ResetPolicy(self, policy, update_mask):
    """Sets the reset field on the policy to True.

    If reset is set to True, no rules can be set on the policy and
    inheritFromParent has to be False. As such, this also deletes all rules on
    the policy and sets inheritFromParent to False.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      update_mask: Specifies whether live/dryrun spec needs to be reset.

    Returns:
      The updated policy.
    """
    new_policy = copy.deepcopy(policy)
    if update_mask is None and new_policy.dryRunSpec:
      raise exceptions.InvalidInputError(
          'update_mask is required if there is dry_run_spec in the request.'
      )
    if self.ShouldUpdateLiveSpec(update_mask):
      if not new_policy.spec:
        new_policy.spec = self.org_policy_api.CreateEmptyPolicySpec()
      new_policy.spec.reset = True
      new_policy.spec.rules = []
      new_policy.spec.inheritFromParent = False
    if self.ShouldUpdateDryRunSpec(update_mask):
      if not new_policy.dryRunSpec:
        new_policy.dryRunSpec = self.org_policy_api.CreateEmptyPolicySpec()
      new_policy.dryRunSpec.reset = True
      new_policy.dryRunSpec.rules = []
      new_policy.dryRunSpec.inheritFromParent = False

    return new_policy

  def GetPolicy(self, policy_name):
    """Get the policy from the service.

    Args:
      policy_name: Name of the policy to be retrieved.

    Returns:
      The retrieved policy, or None if not found.
    """
    try:
      return self.org_policy_api.GetPolicy(policy_name)
    except api_exceptions.HttpNotFoundError:
      return None

  def CreatePolicy(self, policy_name, update_mask):
    """Create the policy on the service if needed.

    Args:
      policy_name: Name of the policy to be created
      update_mask: Specifies whether live/dryrun spec needs to be created.

    Returns:
      The created policy.
    """
    empty_policy = self.org_policy_api.BuildEmptyPolicy(policy_name)
    # Set the reset field to true for sepc/dryrunspec based on the update_mask
    new_policy = self.ResetPolicy(empty_policy, update_mask)

    create_response = self.org_policy_api.CreatePolicy(new_policy)
    log.CreatedResource(policy_name, 'policy')
    return create_response

  def UpdatePolicy(self, policy, policy_name, update_mask):
    """Update the policy on the service.

    Args:
      policy: messages.GoogleCloudOrgpolicy{api_version}Policy, The policy
        object to be updated.
      policy_name: Name of the policy to be updated
      update_mask: Specifies whether live/dryrun spec needs to be updated.

    Returns:
      Returns the updated policy.
    """
    updated_policy = self.ResetPolicy(policy, update_mask)
    if updated_policy == policy:
      return policy

    update_response = self.org_policy_api.UpdatePolicy(
        updated_policy, update_mask
    )
    log.UpdatedResource(policy_name, 'policy')
    return update_response

  def Run(self, args):
    """Retrieves and then creates/updates a policy as needed.

    The following workflow is used:
       Retrieve policy through GetPolicy.
       If policy exists:
           Check policy to see if an update needs to be applied - it could be
           the case that the policy is already in the correct state.
           If policy does not need to be updated:
               No action.
           If policy needs to be updated:
              If the update_mask is set:
                  Update the respective live or dryrun spec through UpdatePolicy
              If the update_mask is not set:
                  If the policy doesn't contain dryrun spec:
                      Update the live spec to reset
                  If the policy contains dryrun spec:
                      Throw an error to specify the what needs to be reset using
                      update_mask
       If policy does not exist:
           If the update_mask is not set:
              Create policy with live spec (with reset field set to true)
              through CreatePolicy.
            If the update_mask is  set:
              Create policy with live/dryrun spec (with reset field set to true)
              through CreatePolicy.

    Note that in the case that a policy exists, an error could be thrown by the
    backend if the policy is updated in between the GetPolicy request and the
    UpdatePolicy request. In the case that a policy does not exist, an error
    could be thrown if the policy did not initially exist but is created in
    between the GetPolicy request and the CreatePolicy request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The policy to return to the user after successful execution.
    """
    self.org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    policy_name = utils.GetPolicyNameFromArgs(args)
    update_mask = utils.GetUpdateMaskFromArgs(args)
    policy = self.GetPolicy(policy_name)
    if not policy:
      return self.CreatePolicy(policy_name, update_mask)
    return self.UpdatePolicy(policy, policy_name, update_mask)


Reset.detailed_help = DETAILED_HELP
