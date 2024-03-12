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
"""`gcloud monitoring policies update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.util.args import repeated


class Update(base.CreateCommand):
  """Updates an alerting policy."""

  detailed_help = {
      'DESCRIPTION': """\
          Updates an alerting policy.

          If `--policy` or `--policy-from-file` are specified:

            * If `--fields` is specified, the only the specified fields will be
              updated.
            * Else, the policy will be replaced with the provided policy. The
              policy can be modified further using the flags from the Policy
              Settings group below.

          Otherwise, the policy will be updated with the values specified in
          the flags from the Policy Settings group.

          For information about the JSON/YAML format of an alerting policy:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.alertPolicies
       """
  }

  @staticmethod
  def Args(parser):
    resources = [
        resource_args.CreateAlertPolicyResourceArg('to be updated.')]
    resource_args.AddResourceArgs(parser, resources)
    flags.AddMessageFlags(parser, 'policy')
    flags.AddFieldsFlagsWithMutuallyExclusiveSettings(
        parser,
        fields_help=('The list of fields to update. Must specify `--policy` or '
                     '`--policy-from-file` if using this flag.'),
        add_settings_func=flags.AddPolicySettingsFlags,
        fields_choices=['disabled', 'notificationChannels'],
        update=True)

  def Run(self, args):
    util.ValidateUpdateArgsSpecified(
        args,
        ['policy', 'policy_from_file', 'display_name', 'enabled',
         'add_notification_channels', 'remove_notification_channels',
         'set_notification_channels',
         'clear_notification_channels', 'documentation', 'documentation_format',
         'documentation_from_file', 'fields', 'update_user_labels',
         'remove_user_labels', 'clear_user_labels'],
        'policy')
    flags.ValidateAlertPolicyUpdateArgs(args)

    client = policies.AlertPolicyClient()
    messages = client.messages

    passed_yaml_policy = False
    policy_ref = args.CONCEPTS.alert_policy.Parse()
    if args.policy or args.policy_from_file:
      passed_yaml_policy = True
      policy = util.GetBasePolicyMessageFromArgs(args, messages.AlertPolicy)
    else:
      # If a full policy isn't given, we want to do Read-Modify-Write.
      policy = client.Get(policy_ref)

    if not args.fields:
      channels = policy.notificationChannels
      new_channels = repeated.ParseResourceNameArgs(
          args, 'notification_channels', lambda: channels,
          util.ParseNotificationChannel)
      enabled = args.enabled if args.IsSpecified('enabled') else None

      fields = []
      util.ModifyAlertPolicy(
          policy,
          messages,
          display_name=args.display_name,
          documentation_content=
          args.documentation or args.documentation_from_file,
          documentation_format=args.documentation_format,
          enabled=enabled,
          channels=new_channels,
          field_masks=fields)

      new_labels = util.ProcessUpdateLabels(
          args,
          'user_labels',
          messages.AlertPolicy.UserLabelsValue,
          policy.userLabels)
      if new_labels:
        policy.userLabels = new_labels
        # TODO(b/73120276): Use field masks per key for label updates.
        fields.append('user_labels')

      # For more robust concurrent updates, use update masks if we're not
      # trying to replace the policy using --policy or --policy-from-file.
      fields = None if passed_yaml_policy else ','.join(sorted(fields))
    else:
      fields = ','.join(args.fields)

    return client.Update(policy_ref, policy, fields)
