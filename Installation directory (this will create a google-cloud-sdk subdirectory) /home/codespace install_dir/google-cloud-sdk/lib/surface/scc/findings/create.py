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
"""Command for creating a Cloud Security Command Center Finding."""

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
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  """Create a Security Command Center finding."""

  detailed_help = {
      "DESCRIPTION": "Create a Security Command Center finding.",
      "EXAMPLES": f"""
          Create an ACTIVE finding `testFinding` with category: XSS_SCRIPTING
          attached to `example-project` under organization `123456` and source
          `5678`:

          $ {{command}} `testFinding` --organization=123456 --source=5678
            --state=ACTIVE --category='XSS_SCRIPTING'
            --event-time=2023-01-11T07:00:06.861Z
            --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project'

          Create an ACTIVE finding `testFinding` attached to `example-project`
          under project `example-project` and source 5678:

            $ {{command}} projects/example-project/sources/5678/findings/testFinding
              --state=ACTIVE --category='XSS_SCRIPTING'
              --event-time=2023-01-11T07:00:06.861Z
              --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project'

          Create an ACTIVE finding `testFinding` attached to `example-project`
          under folder `456` and source `5678`:

            $ {{command}} folders/456/sources/5678/findings/testFinding
              --state=ACTIVE --category='XSS_SCRIPTING'
              --event-time=2023-01-11T07:00:06.861Z
              --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project'

          Create an ACTIVE finding `testFinding` with category: `XSS_SCRIPTING`
          attached to `example-project` under organization `123456`, source
          `5678` and `location=eu`:

          $ {{command}} `testFinding` --organization=123456 --source=5678
            --state=ACTIVE --category='XSS_SCRIPTING'
            --event-time=2023-01-11T07:00:06.861Z
            --resource-name='//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/example-project' --location=eu""",

      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Add shared flags and finding positional argument.
    flags.CreateFindingArg().AddToParser(parser)
    flags.EXTERNAL_URI_FLAG.AddToParser(parser)
    flags.SOURCE_PROPERTIES_FLAG.AddToParser(parser)
    flags.STATE_FLAG.AddToParser(parser)
    flags.EVENT_TIME_FLAG_REQUIRED.AddToParser(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.add_argument(
        "--category",
        help="""
        Taxonomy group within findings from a given source. Example:
        XSS_SCRIPTING""",
        required=True,
    )

    parser.add_argument(
        "--resource-name",
        help="""
        Full resource name of the Google Cloud Platform resource this finding is
        for.""",
        required=True,
    )

  def Run(self, args):
    version = scc_util.GetVersionFromArguments(args, args.finding)
    if version == "v1":
      request = _V1GenerateRequestArgumentsForCreateCommand(args)
    else:
      request = _V2GenerateRequestArgumentsForCreateCommand(args)
    client = securitycenter_client.GetClient(version)
    response = client.organizations_sources_findings.Create(request)
    log.status.Print("Created.")
    return response


def _V2GenerateRequestArgumentsForCreateCommand(args):
  """Generate the request's finding name, finding ID, parent and v2 googleCloudSecuritycenterV2Finding using specified arguments.

  Args:
    args: (argparse namespace)

  Returns:
    req: Modified request
  """
  messages = securitycenter_client.GetMessages("v2")
  request = messages.SecuritycenterOrganizationsSourcesFindingsCreateRequest()
  request.googleCloudSecuritycenterV2Finding = (
      messages.GoogleCloudSecuritycenterV2Finding(
          category=args.category,
          resourceName=args.resource_name,
          state=util.ConvertStateInput(args.state, "v2"),
      )
  )
  request.googleCloudSecuritycenterV2Finding.externalUri = args.external_uri
  if args.IsKnownAndSpecified("source_properties"):
    request.googleCloudSecuritycenterV2Finding.sourceProperties = (
        util.ConvertSourceProperties(args.source_properties, "v2")
    )

  # Convert event_time argument to correct format.
  event_time_dt = times.ParseDateTime(args.event_time)
  request.googleCloudSecuritycenterV2Finding.eventTime = times.FormatDateTime(
      event_time_dt
  )

  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = util.GetFullFindingName(args, "v2")
  request.parent = util.GetSourceParentFromFindingName(finding_name, "v2")
  request.findingId = util.GetFindingIdFromName(finding_name)

  if not request.googleCloudSecuritycenterV2Finding:
    request.googleCloudSecuritycenterV2Finding = (
        messages.GoogleCloudSecuritycenterV2Finding()
    )
  request.googleCloudSecuritycenterV2Finding.name = finding_name
  return request


def _V1GenerateRequestArgumentsForCreateCommand(args):
  """Generate the request's finding name, finding ID, parent and v1 Finding using specified arguments.

  Args:
    args: (argparse namespace)

  Returns:
    req: Modified request
  """
  messages = securitycenter_client.GetMessages("v1")
  request = messages.SecuritycenterOrganizationsSourcesFindingsCreateRequest()
  request.finding = messages.Finding(
      category=args.category,
      resourceName=args.resource_name,
      state=util.ConvertStateInput(args.state, "v1"),
  )
  request.finding.externalUri = args.external_uri
  if args.IsKnownAndSpecified("source_properties"):
    request.finding.sourceProperties = util.ConvertSourceProperties(
        args.source_properties, "v1"
    )

  # Convert event_time argument to correct format.
  event_time_dt = times.ParseDateTime(args.event_time)
  request.finding.eventTime = times.FormatDateTime(event_time_dt)

  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = util.GetFullFindingName(args, "v1")
  request.parent = util.GetSourceParentFromFindingName(finding_name, "v1")
  request.findingId = util.GetFindingIdFromName(finding_name)

  if not request.finding:
    request.finding = messages.Finding()
  request.finding.name = finding_name
  return request
