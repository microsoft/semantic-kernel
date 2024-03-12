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

"""Command for creating a Cloud Security Command Center NotificationConfig."""

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


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  """Create a Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Create a Security Command Center notification config.

      Notification configs that are created with Security Command Center API V2
      and later include a `location` attribute. If a location is not specified,
      the default `global` location is used. For example, the following
      Notification config name has `location=global` attribute:
      `organizations/123/locations/global/notificationConfigs/my-config`.""",
      'EXAMPLES': """\
      Create a notification config test-config under organization 123 for
      findings for pubsub-topic projects/test-project/topics/notification-test
      with a filter on resource name:

        $ {command} test-config --organization=123
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""

      Create a notification config `test-config` under folder `456` for findings
      for pubsub-topic `projects/test-project/topics/notification-test` with a
      filter on resource name:

        $ {command} test-config --folder=456
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""

      Create a notification config `test-config` under project `789` for
      findings for pubsub-topic `projects/test-project/topics/notification-test`
      with a filter on resource name:

        $ {command} test-config --project=789
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""

      Create a notification config `test-config` under organization `123` for
      findings for `pubsub-topic projects/test-project/topics/notification-test`
      with a filter on resource name and `location=eu`

        $ {command} test-config --project=789
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\"" --location=eu
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):

    notifications_flags.PUBSUB_TOPIC_REQUIRED_FLAG.AddToParser(parser)
    notifications_flags.DESCRIPTION_FLAG.AddToParser(parser)
    notifications_flags.FILTER_FLAG.AddToParser(parser)

    notifications_flags.AddNotificationConfigPositionalArgument(parser)
    notifications_flags.AddParentGroup(parser)

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):
    parent = scc_util.GetParentFromNamedArguments(args)
    notification_util.ValidateMutexOnConfigIdAndParent(args, parent)

    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(
        args, args.NOTIFICATIONCONFIGID, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    # Build initial request from versioned messages
    if version == 'v1':
      req = (
          messages.SecuritycenterOrganizationsNotificationConfigsCreateRequest()
      )
      config_name = notification_util.ValidateAndGetNotificationConfigV1Name(
          args
      )
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsNotificationConfigsCreateRequest()
      )
      config_name = notification_util.ValidateAndGetNotificationConfigV2Name(
          args
      )

    req.parent = notification_util.GetParentFromNotificationConfigName(
        config_name
    )
    req.configId = _GetNotificationConfigId(config_name)

    req.notificationConfig = messages.NotificationConfig()
    req.notificationConfig.description = args.description
    req.notificationConfig.pubsubTopic = args.pubsub_topic

    # Use the full config name if provided.
    if '/notificationConfigs/' in args.NOTIFICATIONCONFIGID:
      req.notificationConfig.name = config_name
    else:
      req.notificationConfig.name = args.NOTIFICATIONCONFIGID

    # Set the Streaming Config inside Notification Config.
    streaming_config = messages.StreamingConfig()
    if args.filter is None:
      streaming_config.filter = ''
    else:
      streaming_config.filter = args.filter
    req.notificationConfig.streamingConfig = streaming_config

    # SCC's custom --filter is passing the streaming config filter as part of
    # the request body. However --filter is a global filter flag in gcloud. The
    # --filter flag in gcloud (outside of this command) is used as client side
    # filtering. This has led to a collision in logic as gcloud believes the
    # update is trying to perform client side filtering. Since changing the
    # argument flag would be considered a breaking change, setting args.filter
    # to None in the request hook will skip over the client side filter logic.
    args.filter = None

    if version == 'v1':
      result = client.organizations_notificationConfigs.Create(req)
    else:
      result = client.organizations_locations_notificationConfigs.Create(req)
    log.status.Print('Created.')
    return result.name


def _GetNotificationConfigId(resource_name):
  params_as_list = resource_name.split('/')
  return params_as_list[-1]
