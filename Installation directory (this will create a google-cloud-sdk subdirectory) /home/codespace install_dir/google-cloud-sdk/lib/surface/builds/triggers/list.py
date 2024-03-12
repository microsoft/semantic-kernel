# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""List triggers command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags as build_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class List(base.ListCommand):
  """List Cloud Build triggers for a project."""

  detailed_help = {
      'DESCRIPTION':
          'List Cloud Build triggers for a project.',
      'EXAMPLES': ("""
        To list build triggers, run:

          $ {command}
      """),
  }

  @staticmethod
  def Args(parser):
    build_flags.AddRegionFlag(parser)

  def Run(self, args):
    """Lists the build triggers in a project.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    client = cloudbuild_util.GetClientInstance()

    project = properties.VALUES.core.project.Get(required=True)
    regionprop = properties.VALUES.builds.region.Get()
    location = args.region or regionprop or cloudbuild_util.DEFAULT_REGION

    parent = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=project,
        locationsId=location).RelativeName()

    return client.projects_locations_triggers.List(
        client.MESSAGES_MODULE.CloudbuildProjectsLocationsTriggersListRequest(
            parent=parent)).triggers
