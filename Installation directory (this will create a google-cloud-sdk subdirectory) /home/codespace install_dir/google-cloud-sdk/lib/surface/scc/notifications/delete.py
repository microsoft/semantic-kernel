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
"""Command for deleting a Cloud Security Command Center notification config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.notifications import flags as notifications_flags
from googlecloudsdk.command_lib.scc.notifications import notification_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Delete(base.DeleteCommand):
  """Delete a Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Delete a Security Command Center notification config.

      Notification configs that are created with Security Command Center API V2
      and later include a `location` attribute. If the `location` attribute is
      included in the resource name of a Notification configs, you must specify
      it when referencing the Notification config. For example, the following
      Notification configs name has `location=eu`:
      `organizations/123/locations/eu/notificationConfigs/test-config`.
      """,
      'EXAMPLES': """\
      Delete notification config 'test-config' from organization `123`

        $ {command} test-config --organization=123

      Delete notification config 'test-config' from folder `456`

        $ {command} test-config --folder=456

      Delete notification config 'test-config' from project `789`

        $ {command} test-config --project=789

      Delete notification config 'test-config' with location `global` from
      organization `123`

        $ {command} test-config --organization=123 --location=global

      Delete notification config 'test-config' with `location=eu` from
      organization `123`

        $ {command} test-config --organization=123 --location=eu
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):

    notifications_flags.AddParentGroup(parser)
    notifications_flags.AddNotificationConfigPositionalArgument(parser)

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):

    # Prompt user to confirm deletion.
    console_io.PromptContinue(
        message='Are you sure you want to delete a notification config?\n',
        cancel_on_no=True,
    )

    # Validate mutex after prompt.
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
      req = (
          messages.SecuritycenterOrganizationsNotificationConfigsDeleteRequest()
      )
      req.name = notification_util.ValidateAndGetNotificationConfigV1Name(args)
      result = client.organizations_notificationConfigs.Delete(req)
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsNotificationConfigsDeleteRequest()
      )
      req.name = notification_util.ValidateAndGetNotificationConfigV2Name(args)
      result = client.organizations_locations_notificationConfigs.Delete(req)
    log.status.Print('Deleted.')
    return result
