# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Describe worker pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a worker pool used by Cloud Build."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To get information about a worker pool named `wp1` in region `us-central1`, run:

            $ {command} wp1 --region=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--region',
        required=True,
        help='The Cloud region where the worker pool is.')
    parser.add_argument(
        'WORKER_POOL', help='The ID of the worker pool to describe.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    wp_region = args.region

    release_track = self.ReleaseTrack()
    client = cloudbuild_util.GetClientInstance(release_track)
    messages = cloudbuild_util.GetMessagesModule(release_track)

    parent = properties.VALUES.core.project.Get(required=True)

    wp_name = args.WORKER_POOL

    # Get the workerpool ref
    wp_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.locations.workerPools',
        api_version=cloudbuild_util.RELEASE_TRACK_TO_API_VERSION[release_track],
        params={
            'projectsId': parent,
            'locationsId': wp_region,
            'workerPoolsId': wp_name,
        })

    # Send the Get request
    wp = client.projects_locations_workerPools.Get(
        messages.CloudbuildProjectsLocationsWorkerPoolsGetRequest(
            name=wp_resource.RelativeName()))

    # Format the workerpool name for display
    try:
      wp.name = cloudbuild_util.WorkerPoolShortName(wp.name)
    except ValueError:
      pass  # Must be an old version.

    return wp


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describe a worker pool used by Cloud Build."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Describe a private worker pool used by Cloud Build."""
