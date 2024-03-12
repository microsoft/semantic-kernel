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
"""Command to describe an Apigee application."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class Describe(base.DescribeCommand):
  """Describe an Apigee application."""

  detailed_help = {
      "DESCRIPTION": """
          {description}

          `{command}` retrieves the application's details, including its
          developer, credentials, API products, and other information.
          """,
      "EXAMPLES": """
          To describe an application for the active Cloud Platform project whose
          UUID is ``46d6151e-0000-4dfa-b9c7-c03b8b58bb2f'', run:

              $ {command} 46d6151e-0000-4dfa-b9c7-c03b8b58bb2f

          To describe that application in the Apigee organization ``my-org'',
          formatted as a JSON object, run:

              $ {command} 46d6151e-0000-4dfa-b9c7-c03b8b58bb2f --organization=my-org --format=json
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization.app",
        "Application to be described. To get a list of available applications, "
        "run `{parent_command} list`.",
        argument_name="APPLICATION",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.application.Parse().AsDict()
    return apigee.ApplicationsClient.Describe(identifiers)
