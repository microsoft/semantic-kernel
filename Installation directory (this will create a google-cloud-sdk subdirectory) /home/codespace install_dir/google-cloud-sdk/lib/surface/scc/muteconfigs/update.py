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
"""Command to update a Cloud Security Command Center mute config."""

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
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Security Command Center mute config."""

  detailed_help = {
      "DESCRIPTION": "Update a Security Command Center mute config.",
      "EXAMPLES": """
        Update a mute config with ``ID=test-mute-config'' under
        ``organization=123'' with a filter on category that equals to
        XSS_SCRIPTING:

          $ {command} test-mute-config --organization=123
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\""

        Update a mute config with ``ID=test-mute-config'' under
        ``folder=456'' with a filter on category that equals to XSS_SCRIPTING:

          $ {command} test-mute-config --folder=456
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\""

        Update a mute config with ``ID=test-mute-config'' under
        ``project=789'' with a filter on category that equals to XSS_SCRIPTING:

          $ {command} test-mute-config --project=789
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\""

        Update a mute config with ``ID=test-mute-config'' under
        ``organization=123'' `location=eu`  with a filter on category that
        equals to XSS_SCRIPTING:

          $ {command} test-mute-config --organization=123
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\"" --location=eu""",
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Add flags and positional arguments
    flags.AddParentGroup(parser)
    flags.MUTE_CONFIG_FLAG.AddToParser(parser)
    flags.DESCRIPTION_FLAG.AddToParser(parser)
    flags.FILTER_FLAG.AddToParser(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.add_argument(
        "--update-mask",
        help="""
        Optional: If left unspecified (default), an update-mask is automatically
        created using the flags specified in the command and only those values
        are updated.""",
    )
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(args, args.mute_config)
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsMuteConfigsPatchRequest()

    if version == "v2":
      request.googleCloudSecuritycenterV2MuteConfig = (
          messages.GoogleCloudSecuritycenterV2MuteConfig(
              description=args.description, filter=args.filter
          )
      )
    else:
      request.googleCloudSecuritycenterV1MuteConfig = (
          messages.GoogleCloudSecuritycenterV1MuteConfig(
              description=args.description, filter=args.filter
          )
      )

    # Create update mask if none was specified
    if not args.update_mask:
      computed_update_mask = []
      if args.IsKnownAndSpecified("description"):
        computed_update_mask.append("description")
      if args.IsKnownAndSpecified("filter"):
        computed_update_mask.append("filter")
      request.updateMask = ",".join(computed_update_mask)
    else:
      request.updateMask = args.update_mask

    # Generate name and send request
    request = util.GenerateMuteConfigName(args, request, version)
    request.updateMask = scc_util.CleanUpUserMaskInput(request.updateMask)
    args.filter = ""

    client = securitycenter_client.GetClient(version)
    response = client.organizations_muteConfigs.Patch(request)
    log.status.Print("Updated.")
    return response
