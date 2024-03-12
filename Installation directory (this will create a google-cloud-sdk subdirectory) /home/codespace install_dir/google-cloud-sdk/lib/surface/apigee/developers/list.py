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
"""Command to list all developers in the relevant Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class List(base.ListCommand):
  """List Apigee developers by email address."""

  detailed_help = {
      "DESCRIPTION":
          "{description}",
      "EXAMPLES":
          """
          To list all developers for the active Cloud Platform project, run:

              $ {command}

          To list all developers in an Apigee organization called ``my-org'',
          formatted as JSON objects, run:

              $ {command} --organization=my-org --format=json
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization",
        "Apigee organization whose developers should be listed. If "
        "unspecified, the Cloud Platform project's associated organization "
        "will be used.",
        positional=False,
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])
    parser.display_info.AddFormat("list(email)")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.organization.Parse().AsDict()
    return apigee.DevelopersClient.List(identifiers)
