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
"""`gcloud monitoring snoozes create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import snoozes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Create a new snooze."""

  detailed_help = {
      'DESCRIPTION': """\
          Creates a new snooze. A snooze can be specified as a JSON/YAML value
          passed in as a file through the `--snooze-from-file` flag. A snooze
          can also be specified through command line flags. If a snooze is
          specified through `--snooze-from-file`, and additional flags are
          supplied, the flags will override the snooze's settings.

          For information about the JSON/YAML format of a snooze:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.snoozes
       """,
      'EXAMPLES': """\
          To create a snooze with command-line options, run:

            $ {command} --criteria-policies=LIST_OF_POLICIES
            --display-name=DISPLAY_NAME --start-time=START_TIME
            --end-time=END_TIME

          To create a snooze with a file, run:

            $ {command} --snooze-from-file=MY-FILE

          Sample contents of MY-FILE:

            criteria:
              policies:
              - projects/MY-PROJECT/alertPolicies/MY-POLICY
            interval:
              startTime: '2024-03-01T08:00:00Z'
              endTime: '2024-03-08T04:59:59.500Z'
            displayName: New Snooze
       """
  }

  @staticmethod
  def Args(parser):
    flags.AddFileMessageFlag(parser, 'snooze')
    flags.AddSnoozeSettingsFlags(parser)

  def Run(self, args):
    client = snoozes.SnoozeClient()
    snooze = util.CreateSnoozeFromArgs(args, client.messages)

    project_ref = (
        projects_util.ParseProject(properties.VALUES.core.project.Get()))

    result = client.Create(project_ref, snooze)
    log.CreatedResource(result.name, 'snooze')
    return result
