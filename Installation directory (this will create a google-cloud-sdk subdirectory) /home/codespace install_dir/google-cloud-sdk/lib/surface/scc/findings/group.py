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
"""Command to Filter an organization or source's findings and group them by their specified properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import sys

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.findings import flags
from googlecloudsdk.command_lib.scc.findings import util
from googlecloudsdk.core.util import times


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Group(base.Command):
  """Filter an organization or source's findings and groups them by their specified properties."""

  detailed_help = {
      "DESCRIPTION": """
          To group across all sources provide a '-' as the source id.""",
      "EXAMPLES": """
          Group findings under organization `123456` across all sources by their
          category:

            $ {command} 123456 --group-by="category"

          Group findings under project `example-project` across all sources by
          their category:

            $ {command} projects/example-project --group-by="category"

          Group findings under folders `456` across all sources by their
          category:

            $ {command} folders/456 --group-by="category"

          Group findings under organization `123456` and source `5678`, by their
          category:

            $ {command} 123456 --source=5678 --group-by="category"

          Group ACTIVE findings under organization `123456` and source `5678`,
          by their category:

            $ {command} 123456 --source=5678 --group-by="category"
              --filter="state=\\"ACTIVE\\""

          Group ACTIVE findings under organization `123456` and source `5678`,
          on `2019-01-01T01:00:00 GMT`, by their category:

            $ {command} 123456 --source=5678 --group-by="category"
            --filter="state=\\"ACTIVE\\"" --read-time="2019-01-01T01:00:00Z"

          Group findings under organization `123456` and source `5678` into
          following 3 state_changes (ADDED/CHANGED/UNCHANGED) based on the
          activity during past 24 hours:

            $ {command} 123456 --source=5678 --group-by="state_change"
              --compare-duration=86400s

          Group findings under organization `123456` and `location=eu` across
          all sources by their category:

            $ {command} 123456 --group-by="category" --location=eu""",
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Add shared flags and parent positional argument
    scc_flags.AppendParentArg()[0].AddToParser(parser)
    scc_flags.PAGE_TOKEN_FLAG.AddToParser(parser)
    scc_flags.READ_TIME_FLAG.AddToParser(parser)
    flags.COMPARE_DURATION_FLAG.AddToParser(parser)
    flags.SOURCE_FLAG.AddToParser(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.add_argument(
        "--filter",
        help="""
        Expression that defines the filter to apply across findings. The
        expression is a list of one or more restrictions combined via logical
        operators 'AND' and 'OR'. Parentheses are supported, and 'OR' has higher
        precedence than 'AND'. Restrictions have the form
        '<field> <operator> <value>' and may have a '-' character in front of
        them to indicate negation. Examples include: name,
        source_properties.a_property, security_marks.marks.marka.
        The supported operators are:
        *  '=' for all value types.
        *  '>', '<', '>=', '<=' for integer values.
        *  ':', meaning substring matching, for strings.

        The supported value types are:string literals in quotes, integer
        literals without quotes, boolean literals 'true' and 'false' without
        quotes. Some example filters: 'source_properties.size = 100',
        'category=\\"XSS\\" AND event_time > 10' etc.""",
    )

    parser.add_argument(
        "--group-by",
        help="""
        Expression that defines what findings fields to use for grouping
        (including 'state'). String value should follow SQL syntax: comma
        separated list  of fields. For example: "parent,resource_name".
        The following fields are supported:
        * resource_name
        * category
        * state
        * parent""",
    )

    parser.add_argument(
        "--page-size",
        type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
        help="""
        Maximum number of results to return in a single response. Default is 10,
        minimum is 1, maximum is 1000.""",
    )

  def Run(self, args):
    deprecated_args = ["compare_duration", "read_time"]
    version = util.GetApiVersionUsingDeprecatedArgs(args, deprecated_args)
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsSourcesFindingsGroupRequest()
    request.groupFindingsRequest = messages.GroupFindingsRequest()

    # Populate request fields from args.
    if version == "v1":
      # Include args deprecated in v2.

      if args.IsKnownAndSpecified("compare_duration"):
        # Process compareDuration argument.
        request.groupFindingsRequest.compareDuration = args.compare_duration
        compare_duration_iso = times.ParseDuration(
            request.groupFindingsRequest.compareDuration
        )
        request.groupFindingsRequest.compareDuration = (
            times.FormatDurationForJson(compare_duration_iso)
        )

      if args.IsKnownAndSpecified("read_time"):
        # Get DateTime from string and convert to the format required by API.
        request.groupFindingsRequest.readTime = args.read_time
        read_time_dt = times.ParseDateTime(
            request.groupFindingsRequest.readTime
        )
        request.groupFindingsRequest.readTime = times.FormatDateTime(
            read_time_dt
        )
    request.groupFindingsRequest.filter = args.filter
    request.groupFindingsRequest.groupBy = args.group_by
    request.groupFindingsRequest.pageSize = args.page_size
    request.groupFindingsRequest.pageToken = args.page_token

    request = _GenerateParentForGroupCommand(args, request, version)
    client = securitycenter_client.GetClient(version)
    result = client.organizations_sources_findings.Group(request)
    return result


def _GenerateParentForGroupCommand(args, req, version="v1"):
  """Generate a finding's name and parent using org, source and finding id."""
  util.ValidateMutexOnSourceAndParent(args)
  req.groupFindingsRequest.filter = args.filter
  args.filter = ""

  region_resource_patern = re.compile(
      "(organizations|projects|folders)/[a-z0-9]+/sources/[0-9-]{0,62}/locations/[A-Za-z0-9-]{0,62}$"
  )
  parent = scc_util.GetParentFromPositionalArguments(args)

  if region_resource_patern.match(parent):
    req.parent = parent
    return req

  resource_pattern = re.compile(
      "(organizations|projects|folders)/[a-z0-9]+/sources/[0-9-]{0,62}$"
  )
  if resource_pattern.match(parent):
    args.source = parent
  req.parent = util.GetFullSourceName(args, version)
  return req
