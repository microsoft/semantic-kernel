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
"""Command to describe an environment in the relevant Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe an Apigee deployment environment."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` shows metadata about an Apigee environment.""",
      "EXAMPLES":
          """\
  To describe an environment called ``my-env'' for the active Cloud Platform
  project, run:

      $ {command} my-env

  To describe an environment called ``my-env'', in an organization called
  ``my-org'', as a JSON object, run:

      $ {command} my-env --organization=my-org --format=json
  """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment",
        "Apigee environment to be described. To get a list of available "
        "environments, run `{parent_command} list`.",
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.environment.Parse().AsDict()
    return apigee.EnvironmentsClient.Describe(identifiers)
