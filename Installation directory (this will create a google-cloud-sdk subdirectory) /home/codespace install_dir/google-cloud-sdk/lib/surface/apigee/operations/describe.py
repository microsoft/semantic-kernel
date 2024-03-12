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
"""Command to describe an Apigee long running operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class Describe(base.DescribeCommand):
  """Describe an Apigee long running operation."""

  detailed_help = {
      "EXAMPLES":
          """\
  To describe an operation with UUID ``e267d2c8-04f4-0000-b890-a241de823b0e''
  given that its matching Cloud Platform project has been set in gcloud
  settings, run:

      $ {command} e267d2c8-04f4-0000-b890-a241de823b0e

  To describe an operation with UUID ``e267d2c8-04f4-0000-b890-a241de823b0e''
  within an organization named ``my-org'', formatted as JSON, run:

      $ {command} e267d2c8-04f4-0000-b890-a241de823b0e --organization=my-org --format=json
  """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization.operation",
        "Operation to be described. To get a list of available operations, run "
        "`{{parent_command}} list`.",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.operation.Parse().AsDict()
    return apigee.OperationsClient.Describe(identifiers)
