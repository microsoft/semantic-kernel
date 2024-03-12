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
"""Command to describe an archive deployment in an Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import archives as archive_helper
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe an Apigee archive deployment."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` shows metadata about an Apigee archive deployment.""",
      "EXAMPLES":
          """\
  To describe an archive deployment with the id ``abcdef1234'' in the Apigee
  environment called ``my-env'' using the active Cloud Platform project, run:

      $ {command} abcdef1234 --environment=my-env

  To describe an archive deployment with the id ``1234abcdef'', in the Apigee
  environment called ``my-env'', in an organization called ``my-org'', as a JSON
  object, run:

      $ {command} 1234abcdef --environment=my-env --organization=my-org --format=json
  """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.archive_deployment",
        help_text="Archive deployment to be described. To get a list of "
        "available archive deployments, run `{parent_command} list`.",
        argument_name="archive_deployment",
        positional=True,
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.archive_deployment.Parse().AsDict()
    org = identifiers["organizationsId"]
    archive_name = (
        "organizations/{}/environments/{}/archiveDeployments/{}".format(
            org, identifiers["environmentsId"],
            identifiers["archiveDeploymentsId"]))

    archive_list_response = apigee.ArchivesClient.List(identifiers)
    if not archive_list_response:
      return apigee.ArchivesClient.Describe(identifiers)

    extended_archives = archive_helper.ListArchives(org).ExtendedArchives(
        archive_list_response)
    for a in extended_archives:
      if a["name"] == archive_name:
        return a
    return apigee.ArchivesClient.Describe(identifiers)
