# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command to list all long running operations in the relevant organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


RESPONSE_CONTENT_FIELD = "operations"


class List(base.ListCommand):
  """List Apigee long running operations."""

  detailed_help = {
      "EXAMPLES":
          """\
  To list all operations for the active Cloud Platform project, run:

      $ {command}

  To list all in-progress operations in an Apigee organization called
  ``my-org'', formatted as a JSON array, run:

      $ {command} --organization=my-org --filter="metadata.state=IN_PROGRESS" --format=json
  """}

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization",
        "Organization whose operations should be listed. If unspecified, the "
        "Cloud Platform project's associated organization will be used.",
        positional=False, required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])
    parser.display_info.AddFormat("table(uuid, organization, metadata.state)")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.organization.Parse().AsDict()
    return apigee.OperationsClient.List(identifiers)
