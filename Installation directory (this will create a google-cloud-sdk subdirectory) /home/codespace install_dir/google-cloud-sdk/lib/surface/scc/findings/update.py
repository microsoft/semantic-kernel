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
"""Command to Update a Cloud Security Command Center finding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

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
    base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)
class Update(base.UpdateCommand):
  """Update a Security Command Center finding."""

  detailed_help = {
      "DESCRIPTION": "Update a Security Command Center finding.",
      "EXAMPLES": """
        Update testFinding's state from `ACTIVE` to `INACTIVE`:

          $ {command} `testFinding` --organization=123456 --source=5678
            --state=INACTIVE

        Update testFinding's state from `ACTIVE` to `INACTIVE` using project name
        for example-project:

          $ {command} projects/example-project/sources/5678/findings/testFinding
            --state=INACTIVE

        Update testFinding's state from `ACTIVE` to `INACTIVE` using folder name
        `456`:

          $ {command} folders/456/sources/5678/findings/testFinding
            --state=INACTIVE

        Override all source properties on `testFinding`:

          $ {command} `testFinding` --organization=123456 --source=5678
            --source-properties="propKey1=propVal1,propKey2=propVal2"

        Selectively update a specific source property on `testFinding`:

          $ {command} `testFinding` --organization=123456 --source=5678
            --source-properties="propKey1=propVal1,propKey2=propVal2" --update-mask="source_properties.propKey1"

        Update finding `testFinding` with `location=eu`, state from `ACTIVE` to
        `INACTIVE`:

          $ {command} `testFinding` --organization=123456 --source=5678
            --state=INACTIVE --location=eu""",
      "API REFERENCE": """
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)""",
  }

  @staticmethod
  def Args(parser):
    # Add flags and finding positional argument.
    flags.CreateFindingArg().AddToParser(parser)
    flags.EVENT_TIME_FLAG_NOT_REQUIRED.AddToParser(parser)
    flags.EXTERNAL_URI_FLAG.AddToParser(parser)
    flags.SOURCE_PROPERTIES_FLAG.AddToParser(parser)
    flags.STATE_FLAG.AddToParser(parser)
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)
    parser.add_argument(
        "--update-mask",
        help="""
        Optional: If left unspecified (default), an update-mask is automatically
        created using the flags specified in the command and only those values
        are updated. For example: --external-uri='<some-uri>'
        --event-time='<some-time>' would automatically generate
        --update-mask='external_uri,event_time'. Note that as a result, only
        external-uri and event-time are updated for the given finding and
        everything else remains untouched. If you want to delete
        attributes/properties (that are not being changed in the update command)
        use an empty update-mask (''). That will delete all the mutable
        properties/attributes that aren't specified as flags in the update
        command. In the above example it would delete source-properties.
        State can be toggled from ACTIVE to INACTIVE and vice-versa but it
        cannot be deleted.""",
    )
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(args, args.finding)
    messages = securitycenter_client.GetMessages(version)
    request = messages.SecuritycenterOrganizationsSourcesFindingsPatchRequest()
    request.updateMask = args.update_mask

    # Create update mask if none was specified. The API supports both snake
    # and camel casing. To pass the existing tests we map the arguments from
    # kebab casing to camel casing in the 'mutable_fields' dict.
    if not args.update_mask:
      mutable_fields = {
          "--event-time": "eventTime",
          "--external-uri": "externalUri",
          "--source-properties": "sourceProperties",
          "--state": "state",
      }
      request.updateMask = ""
      for arg in args.GetSpecifiedArgNames():
        if arg in mutable_fields:
          request.updateMask += "," + mutable_fields[arg]

      # Delete the first character of the update mask if it is a comma.
      if request.updateMask.startswith(","):
        request.updateMask = request.updateMask[1:]

    if version == "v1":
      request.finding = messages.Finding()

      request.finding.externalUri = args.external_uri
      if args.source_properties:
        request.finding.sourceProperties = util.ConvertSourceProperties(
            args.source_properties, version
        )
      request.finding.state = util.ConvertStateInput(args.state, version)
    else:
      request.googleCloudSecuritycenterV2Finding = (
          messages.GoogleCloudSecuritycenterV2Finding()
      )

      request.googleCloudSecuritycenterV2Finding.externalUri = args.external_uri
      if args.source_properties:
        request.googleCloudSecuritycenterV2Finding.sourceProperties = (
            util.ConvertSourceProperties(args.source_properties, version)
        )
      request.googleCloudSecuritycenterV2Finding.state = util.ConvertStateInput(
          args.state, version
      )

    request.name = _GenerateFindingName(args, version)
    request.updateMask = scc_util.CleanUpUserMaskInput(request.updateMask)
    request = _UpdateEventTime(args, request, version)
    client = securitycenter_client.GetClient(version)
    response = client.organizations_sources_findings.Patch(request)
    log.status.Print("Updated.")
    return response


def _GenerateFindingName(args, version):
  """Generate a finding's name using org, source and finding id."""
  util.ValidateMutexOnFindingAndSourceAndOrganization(args)
  return util.GetFullFindingName(args, version)


def _UpdateEventTime(args, req, version):
  """Process and include the event time of a finding."""
  # Convert event_time argument to correct format.
  if args.event_time:
    event_time_dt = times.ParseDateTime(args.event_time)
    if version == "v1":
      req.finding.eventTime = times.FormatDateTime(event_time_dt)
    else:
      req.googleCloudSecuritycenterV2Finding.eventTime = times.FormatDateTime(
          event_time_dt
      )

  # All requests require an event time.
  if args.event_time is None:
    # Get current utc time and convert to a string representation.
    event_time = datetime.datetime.now(tz=datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    if version == "v1":
      if req.finding is None:
        req.finding = securitycenter_client.GetMessages().Finding()
      req.finding.eventTime = event_time
    else:
      if req.googleCloudSecuritycenterV2Finding is None:
        req.googleCloudSecuritycenterV2Finding = (
            securitycenter_client.GetMessages().GoogleCloudSecuritycenterV2Finding()
        )
      req.googleCloudSecuritycenterV2Finding.eventTime = event_time
    req.updateMask = req.updateMask + ",event_time"
  return req
