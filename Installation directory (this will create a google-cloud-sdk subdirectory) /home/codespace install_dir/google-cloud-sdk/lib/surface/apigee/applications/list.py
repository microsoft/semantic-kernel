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
"""Command to list Apigee applications."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


# Placeholder developer identifier that should include all developers. No real
# developer ID should have / in it, as they're email addresses.
ANY_DEVELOPER = "/ANY/"


class List(base.ListCommand):
  """List Apigee applications."""

  detailed_help = {
      "EXAMPLES":
          """
          To list all Apigee applications in the active Cloud Platform project,
          run:

              $ {command}

          To list all Apigee applications belonging to the developer
          ``horse@example.com'' in an Apigee organization called ``my-org'',
          formatted as JSON, run:

              $ {command} --developer=horse@example.com --organization=my-org --format=json
          """
  }

  @staticmethod
  def Args(parser):
    fallthroughs = [
        defaults.GCPProductOrganizationFallthrough(),
        defaults.StaticFallthrough("developer", ANY_DEVELOPER)
    ]
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.developer",
        "Apigee organization, and optionally developer, whose applications "
        "should be listed. If developer is not specified, all developers will "
        "be listed.\n\n"
        "To get a list of valid developers, run:\n\n"
        "    $ {grandparent_command} developers list\n\n",
        positional=False,
        fallthroughs=fallthroughs)
    parser.display_info.AddFormat("table(appId, name)")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.developer.Parse().AsDict()
    if identifiers["developersId"] == ANY_DEVELOPER:
      del identifiers["developersId"]
    return apigee.ApplicationsClient.List(identifiers)
