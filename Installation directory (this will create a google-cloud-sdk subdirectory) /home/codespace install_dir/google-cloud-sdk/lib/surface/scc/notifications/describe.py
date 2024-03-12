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
"""Command for describing a Cloud Security Command Center NotificationConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.notifications import notification_util


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Describe(base.DescribeCommand):
  """Describe a Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Describe a Security Command Center notification config.

      Notification configs that are created with Security Command Center API V2
      and later include a `location` attribute. If the `location` attribute is
      included in the resource name of a Notification configs, you must specify
      it when referencing the Notification config. For example, the following
      Notification configs name has `location=eu`:
      `organizations/123/locations/eu/notificationConfigs/test-config`.
      """,
      'EXAMPLES': """\
      Describe notification config 'test-config' from organization `123`

          $ {command} test-config \
              --organization=123

      Describe notification config 'test-config' from folder `456`

          $ {command} test-config \
              --folder=456

      Describe notification config 'test-config' from project `789`

          $ {command} test-config \
              --project=789

      Describe notification config 'test-config' from organization `123` and
      `location=global`

          $ {command} test-config \
              --organization=123 --location=global
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):
    # Notification Config Id is a required argument.
    parser.add_argument(
        'NOTIFICATIONCONFIGID',
        metavar='NOTIFICATION_CONFIG_ID',
        help="""\
         The ID of the notification config. Formatted as
         "organizations/123/notificationConfigs/456" or just "456".
        """,
    )

    # Set org/folder/project as mutually exclusive group.
    resource_group = parser.add_group(required=False, mutex=True)
    resource_group.add_argument(
        '--organization',
        help="""\
            Organization where the notification config resides. Formatted as
            ``organizations/123'' or just ``123''.
            """,
    )
    resource_group.add_argument(
        '--folder',
        help="""\
            Folder where the notification config resides. Formatted as
            ``folders/456'' or just ``456''.
        """,
    )
    resource_group.add_argument(
        '--project',
        help="""\
            Project (ID or number) where the notification config resides.
            Formatted as ``projects/789'' or just ``789''.
        """,
    )
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):

    parent = scc_util.GetParentFromNamedArguments(args)
    notification_util.ValidateMutexOnConfigIdAndParent(args, parent)

    # Determine what version to call from --location and --api-version. The
    # NotificationConfig is a version_specific_existing_resource that may not be
    # accesed through v2 if it currently exists in v1, and vice vesra.
    version = scc_util.GetVersionFromArguments(
        args, args.NOTIFICATIONCONFIGID, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    if version == 'v1':
      req = messages.SecuritycenterOrganizationsNotificationConfigsGetRequest()
      req.name = notification_util.ValidateAndGetNotificationConfigV1Name(args)
      return client.organizations_notificationConfigs.Get(req)
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsNotificationConfigsGetRequest()
      )
      req.name = notification_util.ValidateAndGetNotificationConfigV2Name(args)
      return client.organizations_locations_notificationConfigs.Get(req)
