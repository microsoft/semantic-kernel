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
# pylint: disable=line-too-long
"""Command to list Organization Policies associated with the specified resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import org_policies_base
from googlecloudsdk.command_lib.resource_manager import org_policies_flags as flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Organization Policies associated with the specified resource.

  ## EXAMPLES

  The following command lists all set Organization Policies associated with
  project `foo-project`:

    $ {command} --project=foo-project

  The following command lists all available constraints in addition to set
  Organization Policies associated with project `foo-project`:

    $ {command} --project=foo-project --show-unset
  """

  @staticmethod
  def Args(parser):
    flags.AddParentResourceFlagsToParser(parser)
    base.Argument(
        '--show-unset',
        action='store_true',
        required=False,
        default=False,
        help="""
        Show available constraints. For more information about constraints, see
        https://cloud.google.com/resource-manager/docs/organization-policy/understanding-constraints
        """).AddToParser(parser)
    parser.display_info.AddFormat("""
          table(
            constraint,
            listPolicy.yesno(no="-", yes="SET"),
            booleanPolicy.yesno(no="-", yes="SET"),
            etag
          )
        """)

  def Run(self, args):
    service = org_policies_base.OrgPoliciesService(args)

    response = service.ListOrgPolicies(self.ListOrgPoliciesRequest(args))

    if args.show_unset:
      constraints = service.ListAvailableOrgPolicyConstraints(
          self.ListAvailableOrgPolicyConstraintsRequest(args))
      existing_policies = [policy.constraint for policy in response.policies]
      messages = org_policies.OrgPoliciesMessages()
      for constraint in constraints.constraints:
        if constraint.name not in existing_policies:
          response.policies.append(
              messages.OrgPolicy(constraint=constraint.name))

    return response.policies

  @staticmethod
  def ListOrgPoliciesRequest(args):
    messages = org_policies.OrgPoliciesMessages()
    resource_id = org_policies_base.GetResource(args)
    request = messages.ListOrgPoliciesRequest()
    if args.project:
      return messages.CloudresourcemanagerProjectsListOrgPoliciesRequest(
          projectsId=resource_id, listOrgPoliciesRequest=request)
    elif args.organization:
      return messages.CloudresourcemanagerOrganizationsListOrgPoliciesRequest(
          organizationsId=resource_id, listOrgPoliciesRequest=request)
    elif args.folder:
      return messages.CloudresourcemanagerFoldersListOrgPoliciesRequest(
          foldersId=resource_id, listOrgPoliciesRequest=request)
    return None

  @staticmethod
  def ListAvailableOrgPolicyConstraintsRequest(args):
    messages = org_policies.OrgPoliciesMessages()
    resource_id = org_policies_base.GetResource(args)
    request = messages.ListAvailableOrgPolicyConstraintsRequest()

    if args.project:
      # pylint: disable=line-too-long
      return messages.CloudresourcemanagerProjectsListAvailableOrgPolicyConstraintsRequest(
          projectsId=resource_id,
          listAvailableOrgPolicyConstraintsRequest=request)
    elif args.organization:
      # pylint: disable=line-too-long
      return messages.CloudresourcemanagerOrganizationsListAvailableOrgPolicyConstraintsRequest(
          organizationsId=resource_id,
          listAvailableOrgPolicyConstraintsRequest=request)
    elif args.folder:
      # pylint: disable=line-too-long
      return messages.CloudresourcemanagerFoldersListAvailableOrgPolicyConstraintsRequest(
          foldersId=resource_id,
          listAvailableOrgPolicyConstraintsRequest=request)
    return None
