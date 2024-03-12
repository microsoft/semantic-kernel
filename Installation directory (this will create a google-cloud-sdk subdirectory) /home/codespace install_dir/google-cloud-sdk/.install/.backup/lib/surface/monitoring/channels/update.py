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
"""`gcloud monitoring channels update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import channels
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Update a notification channel."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Updates a notification channel.

          If `--channel-content` or `--channel-content-from-file` are specified:

            * --fields can be specified; only the specified fields will be
              updated.
            * Alternatively, the channel will be replaced with the provided
              channel. The channel can be modified further using the flags
              from the notification channel settings group below.

          Otherwise, the channel will be updated with the values specified in
          the flags from the notification channel settings group.

          For information about the JSON/YAML format of a notification channel:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.notificationChannels

          *Note:* When specifying the Channel as a YAML/JSON, the use of
          `channelLabels` as an alternative name for `labels` is supported.

          ## EXAMPLES
          The following command updates an existing email notification channel to point from
          its original email address to "newaddress@newdomain.tld":

            $ {command} "projects/12345/notificationChannels/67890" \
              --update-channel-labels=email_address=newaddress@newdomain.tld
       """
  }

  @staticmethod
  def Args(parser):
    channel_arg = resource_args.CreateNotificationChannelResourceArg(
        'channel', 'to update')
    resource_args.AddResourceArgs(parser, [channel_arg])
    flags.AddMessageFlags(parser, 'channel-content')
    flags.AddFieldsFlagsWithMutuallyExclusiveSettings(
        parser,
        fields_help='The list of fields to update. Must specify '
                    '`--channel-content` or `--channel-content-from-file` '
                    'if using this flag.',
        add_settings_func=flags.AddNotificationChannelSettingFlags,
        update=True)

  def Run(self, args):
    util.ValidateUpdateArgsSpecified(
        args,
        ['channel_content', 'channel_content_from_file', 'display_name',
         'enabled', 'type', 'description', 'fields', 'update_user_labels',
         'remove_user_labels', 'clear_user_labels', 'update_channel_labels',
         'remove_channel_labels', 'clear_channel_labels'],
        'channel')
    flags.ValidateNotificationChannelUpdateArgs(args)

    client = channels.NotificationChannelsClient()
    messages = client.messages

    channel_ref = args.CONCEPTS.channel.Parse()

    passed_yaml_channel = False
    channel_str = args.channel_content or args.channel_content_from_file
    if channel_str:
      passed_yaml_channel = True
      channel = util.MessageFromString(
          channel_str, messages.NotificationChannel, 'NotificationChannel',
          field_remappings=util.CHANNELS_FIELD_REMAPPINGS)
    else:
      channel = client.Get(channel_ref)

    if not args.fields:
      enabled = args.enabled if args.IsSpecified('enabled') else None

      fields = []
      util.ModifyNotificationChannel(channel,
                                     channel_type=args.type,
                                     display_name=args.display_name,
                                     description=args.description,
                                     enabled=enabled,
                                     field_masks=fields)

      new_user_labels = util.ProcessUpdateLabels(
          args, 'user_labels', messages.NotificationChannel.UserLabelsValue,
          channel.userLabels)
      new_channel_labels = util.ProcessUpdateLabels(
          args, 'channel_labels', messages.NotificationChannel.LabelsValue,
          channel.labels)
      # TODO(b/73120276): Use field masks per key for label updates.
      if new_user_labels:
        channel.userLabels = new_user_labels
        fields.append('user_labels')
      if new_channel_labels:
        channel.labels = new_channel_labels
        fields.append('labels')

      # For more robust concurrent updates, use update masks if we're not
      # trying to replace the channel using --channel-content or
      # --channel-content-from-file.
      fields = None if passed_yaml_channel else ','.join(sorted(fields))
    else:
      fields = ','.join(args.fields)

    return client.Update(channel_ref, channel, fields)
