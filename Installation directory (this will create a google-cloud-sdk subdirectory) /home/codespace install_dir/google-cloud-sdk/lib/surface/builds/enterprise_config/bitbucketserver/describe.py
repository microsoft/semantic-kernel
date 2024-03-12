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
"""List Bitbucket Server configs command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags as build_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.DescribeCommand):
  """Describe a Bitbucket Server config in a Google Cloud project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    build_flags.AddRegionFlag(parser)
    parser.add_argument('CONFIG', help='The id of the Bitbucket Server Config')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    regionprop = properties.VALUES.builds.region.Get()
    bbs_region = args.region or regionprop or cloudbuild_util.DEFAULT_REGION
    parent = properties.VALUES.core.project.Get(required=True)
    config_id = args.CONFIG
    # Get the bitbucket server config ref
    bbs_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.locations.bitbucketServerConfigs',
        api_version='v1',
        params={
            'projectsId': parent,
            'locationsId': bbs_region,
            'bitbucketServerConfigsId': config_id,
        })

    # Send the Get request
    bbs = client.projects_locations_bitbucketServerConfigs.Get(
        messages.CloudbuildProjectsLocationsBitbucketServerConfigsGetRequest(
            name=bbs_resource.RelativeName()))
    return bbs
