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
"""Command to describe an Apigee developer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class Describe(base.DescribeCommand):
  """Describe an Apigee developer."""

  detailed_help = {
      "DESCRIPTION": """
          {description}

          `{command}` retrieves the developer's details, including the
          developer's name, email address, apps, and other information.
          """,
      "EXAMPLES": """
          To describe a developer for the active Cloud Platform project whose
          email address is ``larry@example.com'', run:

              $ {command} larry@example.com

          To describe that developer in the Apigee organization ``my-org'',
          formatted as a JSON object, run:

              $ {command} larry@example.com --organization=my-org --format=json
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization.developer",
        "Email address of the developer to be described. To get a list of "
        "available developers, run `{parent_command} list`.",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.developer.Parse().AsDict()
    return apigee.DevelopersClient.Describe(identifiers)
