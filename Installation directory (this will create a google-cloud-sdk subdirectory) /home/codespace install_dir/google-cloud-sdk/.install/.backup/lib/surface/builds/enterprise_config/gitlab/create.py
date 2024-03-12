# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Create GitLab Enterprise config command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import gitlab_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create a GitLab Enterprise config for use by Cloud Build."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = gitlab_flags.AddGitLabConfigCreateArgs(parser)

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
    gitlab_config = cloudbuild_util.GitLabConfigFromArgs(args)
    parent = properties.VALUES.core.project.Get(required=True)

    # Get the parent project location ref
    parent_resource = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=parent,
        locationsId=args.region)

    # Send the Create request
    created_op = client.projects_locations_gitLabConfigs.Create(
        messages.CloudbuildProjectsLocationsGitLabConfigsCreateRequest(
            parent=parent_resource.RelativeName(),
            gitLabConfig=gitlab_config,
            gitlabConfigId=args.name))

    op_resource = resources.REGISTRY.ParseRelativeName(
        created_op.name, collection='cloudbuild.projects.locations.operations')

    created_config = waiter.WaitFor(
        waiter.CloudOperationPoller(client.projects_locations_gitLabConfigs,
                                    client.projects_locations_operations),
        op_resource, 'Creating GitLab Enterprise config')

    log.CreatedResource(created_config.name, kind='enterprise_config')
    return created_config
