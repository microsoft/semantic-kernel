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
"""Command for listing a finding's security marks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.findings import flags
from googlecloudsdk.command_lib.scc.findings import util
from googlecloudsdk.core.util import times


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class ListMarks(base.ListCommand):
  """List a finding's security marks."""

  detailed_help = {
      "DESCRIPTION": "List a finding's security marks.",
      "EXAMPLES": """
        List all security marks for `testFinding` under organization `123456` and
        source `5678`:

          $ {command} `testFinding` --organization=123456 --source=5678

        List all security marks for `testFinding` under project `example-project`
        and source `5678`:

          $ {command} projects/example-project/sources/5678/findings/testFinding

        List all security marks for `testFinding` under folder `456` and source
        `5678`:

          $ {command} folders/456/sources/5678/findings/testFinding

        List all security marks for `testFinding` under organization `123456`,
        source `5678` and `location=eu`:

          $ {command} `testFinding` --organization=123456 --source=5678
            --location=eu""",
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Remove URI flag.
    base.URI_FLAG.RemoveFromParser(parser)

    # Add shared flags and finding positional argument
    flags.CreateFindingArg().AddToParser(parser)
    scc_flags.PAGE_TOKEN_FLAG.AddToParser(parser)
    scc_flags.READ_TIME_FLAG.AddToParser(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = _GetApiVersion(args)
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsSourcesFindingsListRequest()

    # Populate the request fields from args
    request.pageToken = args.page_token
    if version == "v1" and args.IsKnownAndSpecified("read_time"):
      request.readTime = args.read_time
      # Get DateTime from string and convert to the format required by API.
      read_time_dt = times.ParseDateTime(request.readTime)
      request.readTime = times.FormatDateTime(read_time_dt)

    request = _GenerateParent(args, request, version)
    client = securitycenter_client.GetClient(version)
    list_findings_response = client.organizations_sources_findings.List(request)

    # Get the security marks
    response = util.ExtractSecurityMarksFromResponse(
        list_findings_response.listFindingsResults, args
    )
    return response


def _GenerateParent(args, req, version):
  """Generates a finding's parent and adds filter based on finding name."""
  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = util.GetFullFindingName(args, version)
  req.parent = util.GetSourceParentFromFindingName(finding_name, version)
  req.filter = f"name : \"{util.GetFindingIdFromName(finding_name)}\""
  return req


def _GetApiVersion(args):
  """Determine what version to call from --location and --api-version."""
  deprecated_args = ["compare_duration", "read_time"]
  return scc_util.GetVersionFromArguments(
      args, args.finding, deprecated_args
  )
