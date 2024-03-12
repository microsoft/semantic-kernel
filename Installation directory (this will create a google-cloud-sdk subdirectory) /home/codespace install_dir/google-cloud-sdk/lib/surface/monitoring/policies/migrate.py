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
"""`gcloud monitoring policies migrate` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import channels
from googlecloudsdk.api_lib.monitoring import policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class Migrate(base.CreateCommand):
  """Migrate a Prometheus configuration file to Cloud Monitoring."""

  detailed_help = {'DESCRIPTION': """\
          Creates new alerting policies and/or notification channels based on
          provided Prometheus files. The rules YAML file, which holds the alert
          rules, must be specified as a file through the
          `--policies-from-prometheus-alert-rules-yaml` flag.
       """}

  @staticmethod
  def Args(parser):
    flags.AddMigrateFlags(parser)

  def Run(self, args):
    notification_channel_client = channels.NotificationChannelsClient()
    alert_policy_client = policies.AlertPolicyClient()
    promql_flags = [
        '--policies-from-prometheus-alert-rules-yaml',
        '--channels-from-prometheus-alertmanager-yaml',
    ]
    util.ValidateAtleastOneSpecified(args, promql_flags)
    project_ref = projects_util.ParseProject(
        properties.VALUES.core.project.Get()
    )

    if not console_io.PromptContinue(
        message=(
            'Each call of the migration tool will create a new set of alert'
            ' policies and/or notification channels. Thus, the migration tool'
            ' should not be used to update existing alert policies and/or'
            ' notification channels.'
        ),
        default=False,
    ):
      return

    notification_channels = util.CreateNotificationChannelsFromArgs(
        args, alert_policy_client.messages
    )

    created_channel_names = []
    for channel in notification_channels:
      result = notification_channel_client.Create(project_ref, channel)
      log.CreatedResource(result.name, 'notification channel')
      created_channel_names.append(result.name)

    promql_policies = util.CreatePromQLPoliciesFromArgs(
        args, alert_policy_client.messages, created_channel_names
    )

    policies_results = []
    # might be good to have a rollback mechanism for when a subset of the
    # creations fails. In this case, should we delete the already
    # created policies?
    for policy in promql_policies:
      result = alert_policy_client.Create(project_ref, policy)
      log.CreatedResource(result.name, 'alert policy')
      policies_results.append(result)
    return policies_results
