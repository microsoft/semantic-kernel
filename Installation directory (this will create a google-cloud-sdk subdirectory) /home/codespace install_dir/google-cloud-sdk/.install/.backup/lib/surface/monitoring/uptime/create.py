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
"""`gcloud monitoring uptime create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import uptime
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Create a new uptime check or synthetic monitor."""

  detailed_help = {
      "DESCRIPTION": """\
          Create a new uptime check or synthetic monitor.

          Flags only apply to uptime checks unless noted that they apply to
          synthetic monitors.

          For information about the JSON/YAML format of an uptime check:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.uptimeCheckConfigs
       """,
      "EXAMPLES": """\
          To create an uptime check against a URL, run:

            $ {command} DISPLAY_NAME --resource-type=uptime-url
            --resource-labels=host=google.com,project_id=PROJECT_ID

          To create a synthetic monitor, run:

            $ {command} SYNTHETIC_MONITOR_NAME
            --synthetic-target=projects/PROJECT_ID/locations/REGION/functions/FUNCTION_NAME
       """,
  }

  @staticmethod
  def Args(parser):
    flags.AddDisplayNameFlag(
        parser, "uptime check or synthetic monitor", positional=True
    )
    flags.AddUptimeSettingsFlags(parser)

  def Run(self, args):
    client = uptime.UptimeClient()
    uptime_check = util.CreateUptimeFromArgs(args, client.messages)
    project_ref = projects_util.ParseProject(
        properties.VALUES.core.project.Get()
    )
    result = client.Create(project_ref, uptime_check)
    log.CreatedResource(result.name, "uptime")
    return result
