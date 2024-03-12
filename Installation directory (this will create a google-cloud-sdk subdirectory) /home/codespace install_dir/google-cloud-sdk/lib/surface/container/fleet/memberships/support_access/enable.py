# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""The enable command for adding anthos support RBACs to the cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.command_lib.container.fleet.memberships import errors
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import properties

ANTHOS_SUPPORT_USER = 'service-{project_number}@gcp-sa-{instance_name}anthossupport.iam.gserviceaccount.com'
ROLE_TYPE = 'ANTHOS_SUPPORT'
ROLE_BINDING_ID = 'gke-fleet-support-access'
RESOURCE_NAME_FORMAT = '{membership_name}/rbacrolebindings/{rbacrolebinding_id}'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Enable(base.CreateCommand):
  """Enable support access for the specified membership.

  ## EXAMPLES

    To enable support access for membership `my-membership` run:

      $ {command} my-membership

  """

  def GetAnthosSupportUser(self, project_id):
    """Get P4SA account name for Anthos Support when user not specified.

    Args:
      project_id: the project ID of the resource.

    Returns:
      the P4SA account name for Anthos Support.
    """
    project_number = projects_api.Get(
        projects_util.ParseProject(project_id)
    ).projectNumber
    hub_endpoint_override = util.APIEndpoint()
    if hub_endpoint_override == util.PROD_API:
      return ANTHOS_SUPPORT_USER.format(
          project_number=project_number, instance_name=''
      )
    elif hub_endpoint_override == util.STAGING_API:
      return ANTHOS_SUPPORT_USER.format(
          project_number=project_number, instance_name='staging-'
      )
    elif hub_endpoint_override == util.AUTOPUSH_API:
      return ANTHOS_SUPPORT_USER.format(
          project_number=project_number, instance_name='autopush-'
      )
    else:
      raise errors.UnknownApiEndpointOverrideError('gkehub')

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        membership_help=textwrap.dedent("""\
          The membership name that you want to enable support access for.
        """),
        location_help=textwrap.dedent("""\
          The location of the membership resource, e.g. `us-central1`.
          If not specified, defaults to `global`.
        """),
        membership_required=True,
        positional=True)

  def Run(self, args):
    project_id = properties.VALUES.core.project.GetOrFail()
    membership_name = resources.ParseMembershipArg(args)
    user = self.GetAnthosSupportUser(project_id)
    name = RESOURCE_NAME_FORMAT.format(
        membership_name=membership_name, rbacrolebinding_id=ROLE_BINDING_ID)

    fleet_client = client.FleetClient(release_track=self.ReleaseTrack())
    return fleet_client.CreateMembershipRbacRoleBinding(
        name, ROLE_TYPE, user, None)
