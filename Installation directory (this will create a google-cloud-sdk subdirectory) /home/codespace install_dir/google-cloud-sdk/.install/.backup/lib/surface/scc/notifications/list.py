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
"""Command for listing Cloud Security Command Center Notification Configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class List(base.ListCommand):
  """List Security Command Center notification configs."""

  detailed_help = {
      'DESCRIPTION': """List Security Command Center notification configs.

      Notification Configs that are created with Security Command Center API V2
      and later include a `location` attribute. Include the `--location` flag to
      list Notification Configs with `location` attribute other than `global`.
      """,
      'EXAMPLES': """\
      List notification configs from organization `123`

        $ {command} 123
        $ {command} organizations/123

      List notification configs from folder `456`

        $ {command} folders/456

      List notification configs from project `789`

        $ {command} projects/789

      List notification configs from organization `123` and `location=eu`

        $ {command} 123 --location=eu
        $ {command} organizations/123 --location=locations/eu
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):
    # Remove URI flag.
    base.URI_FLAG.RemoveFromParser(parser)

    # Add shared flags and parent positional argument.
    scc_flags.AppendParentArg()[0].AddToParser(parser)

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):
    # Determine what version to call from --api-version.
    version = scc_util.GetVersionFromArguments(
        args, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    if version == 'v1':
      request = (
          messages.SecuritycenterOrganizationsNotificationConfigsListRequest()
      )
      request.parent = scc_util.GetParentFromPositionalArguments(args)
      endpoint = client.organizations_notificationConfigs
    else:
      request = (
          messages.SecuritycenterOrganizationsLocationsNotificationConfigsListRequest()
      )
      location = scc_util.ValidateAndGetLocation(args, 'v2')
      request.parent = f'{scc_util.GetParentFromPositionalArguments(args)}/locations/{location}'
      endpoint = client.organizations_locations_notificationConfigs
    request.pageSize = args.page_size

    # Automatically handle pagination. All notifications are returned regardless
    # of --page-size argument.
    return list_pager.YieldFromList(
        endpoint,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='notificationConfigs',
    )
