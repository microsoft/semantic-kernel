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
"""Command to Create a Cloud Security Command Center mute config."""

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
class Create(base.CreateCommand):
  """Create a Security Command Center mute config."""

  detailed_help = {
      "DESCRIPTION": "Create a Security Command Center mute config.",
      "EXAMPLES": """
        To create a mute config ``test-mute-config'' given organization ``123''
        with a filter on category that equals to ``XSS_SCRIPTING'', run:

          $ {command} test-mute-config --organization=123
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\""

        To create a mute config ``test-mute-config'' given folder ``456'' with a
        filter on category that equals to ``XSS_SCRIPTING'', run:

          $ {command} test-mute-config --folder=456
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\""

        To create a mute config ``test-mute-config'' given project ``789'' with a
        filter on category that equals to ``XSS_SCRIPTING'', run:

          $ {command} test-mute-config --project=789
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\""

        To create a mute config ``test-mute-config'' given organization ``123'',
        `location=eu` with a filter on category that equals to ``XSS_SCRIPTING'',
        run:

          $ {command} test-mute-config --organization=123
            --description="This is a test mute config"
            --filter="category=\\"XSS_SCRIPTING\\"" --location=eu""",
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Add flags and positional arguments.
    flags.MUTE_CONFIG_FLAG.AddToParser(parser)
    flags.AddParentGroup(parser)
    flags.DESCRIPTION_FLAG.AddToParser(parser)
    flags.FILTER_FLAG.AddToParser(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(args, args.mute_config)
    # Build request from args.
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsMuteConfigsCreateRequest()
    if version == "v2":
      request.googleCloudSecuritycenterV2MuteConfig = (
          messages.GoogleCloudSecuritycenterV2MuteConfig(
              filter=args.filter,
              description=args.description,
              type=messages.GoogleCloudSecuritycenterV2MuteConfig.TypeValueValuesEnum.STATIC,
          )
      )
    else:
      request.googleCloudSecuritycenterV1MuteConfig = (
          messages.GoogleCloudSecuritycenterV1MuteConfig(
              filter=args.filter, description=args.description
          )
      )
    request = _GenerateMuteConfig(args, request, version)
    client = securitycenter_client.GetClient(version)
    response = client.organizations_muteConfigs.Create(request)
    log.status.Print("Created.")
    return response


def _GenerateMuteConfig(args, req, version="v1"):
  """Updates parent and Generates a mute config."""
  req.parent = util.ValidateAndGetParent(args)
  if req.parent is not None:
    if version == "v2":
      req.parent = util.ValidateAndGetRegionalizedParent(args, req.parent)
    req.muteConfigId = util.ValidateAndGetMuteConfigId(args)
  else:
    args.location = scc_util.ValidateAndGetLocation(args, version)
    mute_config = util.ValidateAndGetMuteConfigFullResourceName(
        args, version
    )
    req.muteConfigId = util.GetMuteConfigIdFromFullResourceName(mute_config)
    req.parent = util.GetParentFromFullResourceName(mute_config, version)
  args.filter = ""
  return req
