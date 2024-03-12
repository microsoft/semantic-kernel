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
"""`gcloud monitoring policies create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Create a new alerting policy."""

  detailed_help = {
      'DESCRIPTION': """\
          Creates a new alerting policy. An alert policy can be specified as a
          JSON/YAML value passed in as a string through the `--policy` flag or
          as a file through the `--policy-from-file` flag. A basic policy can
          also be specified through command line flags. If a policy is specified
          through `--policy` or `--policy-from-file`, and additional flags are
          supplied, the flags will override the policy's settings and a
          specified condition will be appended to the list of conditions.

          For information about the JSON/YAML format of an alerting policy:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.alertPolicies
       """
  }

  @staticmethod
  def Args(parser):
    flags.AddMessageFlags(parser, 'policy')
    flags.AddPolicySettingsFlags(parser)
    flags.AddConditionSettingsFlags(parser)
    channels_resource_arg = resource_args.CreateNotificationChannelResourceArg(
        arg_name='--notification-channels',
        extra_help="""\
            to be added to the policy. These should be the resource names (not
            the display name) of the channels. Acceptable formats are:

            * Channel Name: `my-channel`
              * The project specified through `--project` or the default
                project defined by the `core/project` property will be used,
                in that order.
            * Channel Relative Name:
                `projects/my-project/notificationChannels/channel-id0`
            * Channel URI:
                https://monitoring.googleapis.com/v3/projects/my-project/notificationChannels/channel-id0
            """,
        required=False,
        plural=True)
    resource_args.AddResourceArgs(parser, [channels_resource_arg])

  def Run(self, args):
    client = policies.AlertPolicyClient()
    messages = client.messages
    policy = util.CreateAlertPolicyFromArgs(args, client.messages)

    if args.user_labels:
      policy.userLabels = util.ParseCreateLabels(
          args.user_labels, messages.AlertPolicy.UserLabelsValue)

    project_ref = (
        projects_util.ParseProject(properties.VALUES.core.project.Get()))

    result = client.Create(project_ref, policy)
    log.CreatedResource(result.name, 'alert policy')
    return result
