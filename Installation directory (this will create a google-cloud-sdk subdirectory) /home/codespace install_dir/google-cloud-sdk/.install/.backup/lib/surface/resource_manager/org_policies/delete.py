# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to delete an Organization Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import org_policies_base
from googlecloudsdk.command_lib.resource_manager import org_policies_flags as flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class DeletePolicy(base.DeleteCommand):
  """Delete an Organization Policy.

  Deletes an Organization Policy associated with the specified resource.

  ## EXAMPLES

  The following command clears an Organization Policy for constraint
  `serviceuser.services` on project `foo-project`:

    $ {command} serviceuser.services --project=foo-project
  """

  @staticmethod
  def Args(parser):
    flags.AddIdArgToParser(parser)
    flags.AddParentResourceFlagsToParser(parser)

  def Run(self, args):
    service = org_policies_base.OrgPoliciesService(args)

    result = service.ClearOrgPolicy(self.ClearOrgPolicyRequest(args))
    log.DeletedResource(result)

  @staticmethod
  def ClearOrgPolicyRequest(args):
    messages = org_policies.OrgPoliciesMessages()
    resource_id = org_policies_base.GetResource(args)
    request = messages.ClearOrgPolicyRequest(
        constraint=org_policies.FormatConstraint(args.id))

    if args.project:
      return messages.CloudresourcemanagerProjectsClearOrgPolicyRequest(
          projectsId=resource_id, clearOrgPolicyRequest=request)
    elif args.organization:
      return messages.CloudresourcemanagerOrganizationsClearOrgPolicyRequest(
          organizationsId=resource_id, clearOrgPolicyRequest=request)
    elif args.folder:
      return messages.CloudresourcemanagerFoldersClearOrgPolicyRequest(
          foldersId=resource_id, clearOrgPolicyRequest=request)
    return None
