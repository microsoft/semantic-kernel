# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Describe build command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Describe(base.DescribeCommand):
  """Get information about a particular build."""

  detailed_help = {
      'DESCRIPTION': 'Get information about a particular build.',
      'EXAMPLES': ("""
            To describe a build `123-456-789`:

                $ {command} '123-456-789'
            """),
  }

  @staticmethod
  def Args(parser):
    flags.AddRegionFlag(parser)
    flags.AddBuildArg(parser, intro='The build to describe.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    build_region = args.region or cloudbuild_util.DEFAULT_REGION

    client = cloudbuild_util.GetClientInstance()

    build_ref = resources.REGISTRY.Parse(
        args.build,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
            'locationsId': build_region,
            'buildsId': args.build,
        },
        collection='cloudbuild.projects.locations.builds')
    return client.projects_locations_builds.Get(
        client.MESSAGES_MODULE.CloudbuildProjectsLocationsBuildsGetRequest(
            name=build_ref.RelativeName()))
