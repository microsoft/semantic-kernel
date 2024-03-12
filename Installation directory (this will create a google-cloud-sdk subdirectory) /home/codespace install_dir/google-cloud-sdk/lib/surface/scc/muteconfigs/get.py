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

"""Command to Get a Cloud Security Command Center mute config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.muteconfigs import flags
from googlecloudsdk.command_lib.scc.muteconfigs import util
from googlecloudsdk.core import properties


# TODO: b/308476775 - Migrate Get command usage to Describe
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class Get(base.Command):
  """Get a Security Command Center mute config."""

  detailed_help = {
      "DESCRIPTION": "Get a Security Command Center mute config.",
      "EXAMPLES": """
        To get a mute config given organization ``123'' with id ``test-mute-config'', run:

        $ {command} test-mute-config --organization=123

      To get a mute config given folder ``456'' with id
      ``test-mute-config'', run:

        $ {command} test-mute-config --folder=456

      To get a mute config given project ``789'' with id
      ``test-mute-config'', run:

        $ {command} test-mute-config --project=789

      To get a mute config given organization ``123'' with id
      ``test-mute-config'' and `location=eu`, run:

        $ {command} test-mute-config --organization=123 --location=eu""",
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Add flags and positional arguments.
    flags.MUTE_CONFIG_FLAG.AddToParser(parser)
    flags.AddParentGroup(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(args, args.mute_config)
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsMuteConfigsGetRequest()

    # Generate name and send request if the user continues.
    request = util.GenerateMuteConfigName(args, request, version)
    client = securitycenter_client.GetClient(version)

    response = client.organizations_muteConfigs.Get(request)
    return response
