# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""`gcloud alpha scc settings services modules update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.settings import flags
from googlecloudsdk.command_lib.scc.settings import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Enable(base.UpdateCommand):
  """Update a module config in Security Command Center(SCC)."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Update a module config in Security Command Center(SCC).
          """,
      'EXAMPLES':
          """\
          To update the "CONFIGURABLE_BAD_DOMAIN" module in service EVENT_THREAT_DETECTION of organization "12345", run:

            $ {command} --organization=12345  --service=EVENT_THREAT_DETECTION --module=CONFIGURABLE_BAD_DOMAIN --enablement-state=ENABLED --config='{
                "domains": {
                  "domain1": {
                    "ed11": "ed-1",
                    "ed12": "ed-2"
                  }
                },
                "metadata": {
                  "module_name": "etd_bad_domain",
                  "severity": "CRITICAL"
                }
              }'

          To clear the config value and disable the module in the "CONFIGURABLE_BAD_DOMAIN" module in service EVENT_THREAT_DETECTION of organization "12345", run:

            $ {command} --organization=12345  --service=EVENT_THREAT_DETECTION --module=CONFIGURABLE_BAD_DOMAIN --enablement-state=DISABLED --clear-config
      """
  }

  @staticmethod
  def Args(parser):
    flags.ExtractRequiredFlags(parser)
    flags.AddServiceArgument(parser)
    flags.AddModuleArgument(parser)
    flags.ExtractModuleConfigFlags(parser)
    flags.AddModuleEnablementArgument(parser)

  def Run(self, args):
    """Call corresponding APIs based on the flag."""
    return utils.SettingsClient().UpdateModuleConfig(args)
