# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""`gcloud monitoring channels create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import channels
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a new notification channel."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Creates a new notification channel. A channel can be specified as
          JSON/YAML passed in as a string through the `--channel-content` flag
          or as a file through the `--channel-content-from-file` flag.
          A basic channel can also be specified through command line flags. If
          a channel is specified through `--channel-content` or
          `--channel-content-from-file`, and additional flags are supplied, the
          flags will override the given channel's settings.

          For information about the JSON/YAML format of a notification channel:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.notificationChannels

          Additional documentation can for this operation can be found at:
          https://cloud.google.com/monitoring/alerts/using-channels-api

          ## EXAMPLES
          The following commands setup both email and SMS notification channels for the team lead. Note
          that the display name and description focus on the purpose/semantics of the channel rather
          than its destination. This is a best-practice that facilitates swapping/updating notification
          channels in-place (such as when users change teams, projects, roles, companies, etc.) with
          minimal impact to the alerting policies that reference the existing channels. It is also
          a best practice to supply at least two channels of different types for a given person.

            $ {command} \
              --display-name="Foo Team Lead (Primary)" \
              --description="Primary contact method for the Foo team lead" \
              --type=email \
              --user-labels=team=foo,role=lead,ord=1 \
              --channel-labels=email_address=user@somedomain.tld

            $ {command} \
              --display-name="Foo Team Lead (Secondary)" \
              --description="Secondary contact method for the Foo team lead" \
              --type=sms \
              --user-labels=team=foo,role=lead,ord=2 \
              --channel-labels=number=123-456-7890
       """
  }

  @staticmethod
  def Args(parser):
    flags.AddMessageFlags(parser, 'channel-content')
    flags.AddNotificationChannelSettingFlags(parser)

  def Run(self, args):
    client = channels.NotificationChannelsClient()
    messages = client.messages

    channel = util.GetNotificationChannelFromArgs(args, messages)

    if args.user_labels:
      channel.userLabels = util.ParseCreateLabels(
          args.user_labels, messages.NotificationChannel.UserLabelsValue)
    if args.channel_labels:
      channel.labels = util.ParseCreateLabels(
          args.channel_labels, messages.NotificationChannel.LabelsValue)

    project_ref = (
        projects_util.ParseProject(properties.VALUES.core.project.Get()))

    result = client.Create(project_ref, channel)
    log.CreatedResource(result.name, 'notification channel')
    return result
