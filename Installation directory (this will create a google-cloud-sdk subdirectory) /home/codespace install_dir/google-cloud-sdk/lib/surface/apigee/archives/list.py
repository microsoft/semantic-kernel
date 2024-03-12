# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Command to list all Apigee archive deployments in an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import archives as archive_helper
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Apigee archive deployments."""

  detailed_help = {
      "EXAMPLES":
          """\
  To list all archive deployments, in an environment called ``my-env'', for the
  active Cloud Platform project, run:

      $ {command} --environment=my-env

  To list all archive deployments, for an environment named ``my-env'', in an
  organization called ``my-org'', run:

      $ {command} --environment=my-env --organization=my-org

  To list all archive deployments formatted as a JSON array, run:

      $ {command} --environment=my-env --format=json
  """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment",
        "Apigee environment whose archive deployments should be listed.",
        positional=False,
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])
    # The response is a JSON array of archive deployment descriptors, so the
    # array needs to be flattened to display as a table.
    parser.display_info.AddFlatten(["archiveDeployments[]"])
    # Cloud SDK projections can be used to format each column of the display
    # table:
    # https://cloud.google.com/sdk/gcloud/reference/topic/projections
    # The "ARCHIVE ID" column scopes the resource path in the "name" field of
    # the API response to only show the id of the archive deployment.
    archive_id_col = ("archiveDeployments.name.scope(archiveDeployments)"
                      ":label='ARCHIVE ID'")
    # The "ENVIORNMENT" column scopes the resource path in the "name" field of
    # the API response to only show the Apigee environment id.
    env_id_col = ("archiveDeployments.name.scope(environments).segment(0)"
                  ":label=ENVIRONMENT")
    # The "CREATED AT" column formats the posix epoch in the "createdAt" field
    # of the API response into a human-readable date format.
    created_col = ("archiveDeployments.createdAt.date("
                   "format='%Y-%m-%d %H:%M:%S %Z', unit=1000000, tz=LOCAL)"
                   ":label='DEPLOYED AT'")
    # The labels field is a list of key/value pairs so it is flattened to
    # display in the table.
    labels_col = "archiveDeployments.labels.flatten()"

    # The status column uses operation metadata and timestamps to determine
    # the current status of the archive deployment.
    status_col = ("archiveDeployments.operationStatus:label='OPERATION STATUS'")
    cols = ", ".join(
        [archive_id_col, env_id_col, created_col, labels_col, status_col])
    # Format the column definitions into a table.
    table_fmt = "table({})".format(cols)
    parser.display_info.AddFormat(table_fmt)

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.environment.Parse().AsDict()
    org = identifiers["organizationsId"]

    archive_response = apigee.ArchivesClient.List(identifiers)

    extended_archives = archive_helper.ListArchives(org).ExtendedArchives(
        archive_response)

    return {"archiveDeployments": extended_archives}
