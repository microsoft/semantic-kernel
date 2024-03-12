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
"""Command to bulk mute Security Command Center findings based on a filter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.findings import util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class BulkMute(base.Command):
  """Bulk mute Security Command Center findings based on a filter."""

  detailed_help = {
      "DESCRIPTION": (
          "Bulk mute Security Command Center findings based on a filter."
      ),
      "EXAMPLES": """
      To bulk mute findings given organization ``123'' based on a filter on
      category that equals ``XSS_SCRIPTING'', run:

        $ {command} --organization=organizations/123
          --filter="category=\\"XSS_SCRIPTING\\""

      To bulk mute findings given folder ``123'' based on a filter on category
      that equals ``XSS_SCRIPTING'', run:

        $ {command} --folder=folders/123 --filter="category=\\"XSS_SCRIPTING\\""

      To bulk mute findings given project ``123'' based on a filter on category
      that equals ``XSS_SCRIPTING'', run:

        $ {command} --project=projects/123
          --filter="category=\\"XSS_SCRIPTING\\""

      To bulk mute findings given organization ``123'' based on a filter on
      category that equals ``XSS_SCRIPTING'' and `location=eu` run:

        $ {command} --organization=organizations/123
          --filter="category=\\"XSS_SCRIPTING\\"" --location=locations/eu
      """,
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Create argument group for parent, this can be org | folder | project.
    parent_group = parser.add_group(mutex=True, required=True)
    parent_group.add_argument(
        "--organization",
        help="""
        Organization where the findings reside. Formatted as
        ``organizations/123'' or just ``123''.""",
    )

    parent_group.add_argument(
        "--folder",
        help="""
        Folder where the findings reside. Formatted as ``folders/456'' or just
        ``456''.""",
    )
    parent_group.add_argument(
        "--project",
        help="""
        Project (id or number) where the findings reside. Formatted as
        ``projects/789'' or just ``789''.""",
    )

    parser.add_argument(
        "--filter",
        help="The filter string which will applied to findings being muted.",
    )
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):
    version = scc_util.GetVersionFromArguments(args)
    # Create the request and include the filter from args.
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsFindingsBulkMuteRequest()
    request.bulkMuteFindingsRequest = messages.BulkMuteFindingsRequest(
        filter=args.filter
    )
    request.parent = util.ValidateAndGetParent(args)
    args.filter = ""

    if version == "v2":
      request.parent = util.ValidateLocationAndGetRegionalizedParent(
          args, request.parent
      )

    client = securitycenter_client.GetClient(version)
    return client.organizations_findings.BulkMute(request)
