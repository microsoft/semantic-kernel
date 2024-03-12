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
"""Command to describe an Organization Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import exceptions
from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import org_policies_base
from googlecloudsdk.command_lib.resource_manager import org_policies_flags as flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an Organization Policy.

  Describes an Organization Policy associated with the specified resource.

  ## EXAMPLES

  The following command retrieves an Organization Policy
  for constraint `serviceuser.services` on project `foo-project`:

    $ {command} serviceuser.services --project=foo-project

  The following command retrieves the effective Organization Policy
  for constraint `serviceuser.services` on project `foo-project`:

    $ {command} serviceuser.services --project=foo-project --effective
  """

  POLICY_V2_WARNING = ('This policy has been set with Tags through Organization'
                       ' Policy V2 API, please use `gcloud org-policies` '
                       'commands instead.')

  @staticmethod
  def Args(parser):
    flags.AddIdArgToParser(parser)
    flags.AddParentResourceFlagsToParser(parser)
    base.Argument(
        '--effective',
        action='store_true',
        required=False,
        default=False,
        help='Show the effective policy.').AddToParser(parser)

  def Run(self, args):
    service = org_policies_base.OrgPoliciesService(args)

    if not args.effective:
      response = service.GetOrgPolicy(
          org_policies_base.GetOrgPolicyRequest(args))
      if response.version is not None and response.version == 2:
        raise exceptions.ResourceManagerError(self.POLICY_V2_WARNING)
    else:
      response = service.GetEffectiveOrgPolicy(
          self.GetEffectiveOrgPolicyRequest(args))
    return response

  @staticmethod
  def GetEffectiveOrgPolicyRequest(args):
    m = org_policies.OrgPoliciesMessages()
    resource_id = org_policies_base.GetResource(args)
    request = m.GetEffectiveOrgPolicyRequest(
        constraint=org_policies.FormatConstraint(args.id))

    if args.project:
      return m.CloudresourcemanagerProjectsGetEffectiveOrgPolicyRequest(
          projectsId=resource_id, getEffectiveOrgPolicyRequest=request)
    elif args.organization:
      return m.CloudresourcemanagerOrganizationsGetEffectiveOrgPolicyRequest(
          organizationsId=resource_id, getEffectiveOrgPolicyRequest=request)
    elif args.folder:
      return m.CloudresourcemanagerFoldersGetEffectiveOrgPolicyRequest(
          foldersId=resource_id, getEffectiveOrgPolicyRequest=request)
    return None
