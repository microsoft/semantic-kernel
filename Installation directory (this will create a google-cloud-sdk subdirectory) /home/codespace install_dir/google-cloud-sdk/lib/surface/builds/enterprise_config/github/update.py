# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Update github enterprise config command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import githubenterprise_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update github enterprise config used by Cloud Build.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = githubenterprise_flags.AddGitHubEnterpriseConfigUpdateArgs(parser)
    parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            host_url,
            app_id
          )
        """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated github enterprise resource.
    """

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    config_id = args.CONFIG
    ghe = cloudbuild_util.GitHubEnterpriseConfigFromArgs(args, True)
    regionprop = properties.VALUES.builds.region.Get()
    location = args.region or regionprop or cloudbuild_util.DEFAULT_REGION

    parent = properties.VALUES.core.project.Get(required=True)

    # Get the github enterprise config ref
    ghe_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.locations.githubEnterpriseConfigs',
        api_version='v1',
        params={
            'projectsId': parent,
            'githubEnterpriseConfigsId': config_id,
            'locationsId': location,
        },
    )

    update_mask = cloudbuild_util.MessageToFieldPaths(ghe)
    update_mask.sort()
    req = (
        messages.CloudbuildProjectsLocationsGithubEnterpriseConfigsPatchRequest(
            name=ghe_resource.RelativeName(),
            gitHubEnterpriseConfig=ghe,
            updateMask=','.join(update_mask),
        )
    )
    # Send the Update request
    updated_op = client.projects_locations_githubEnterpriseConfigs.Patch(req)

    op_resource = resources.REGISTRY.ParseRelativeName(
        updated_op.name, collection='cloudbuild.projects.locations.operations'
    )

    updated_ghe = waiter.WaitFor(
        waiter.CloudOperationPoller(
            client.projects_locations_githubEnterpriseConfigs,
            client.projects_locations_operations,
        ),
        op_resource,
        'Updating GitHub Enterprise Config',
    )

    log.UpdatedResource(ghe_resource)

    return updated_ghe
