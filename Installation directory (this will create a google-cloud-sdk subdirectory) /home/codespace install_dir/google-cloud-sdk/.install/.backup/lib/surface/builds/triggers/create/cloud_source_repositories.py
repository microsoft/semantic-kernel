# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Create Cloud Source Repositories trigger command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import trigger_config as trigger_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source import resource_args as repo_resource
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class CreateCSR(base.CreateCommand):
  """Create a build trigger from a Cloud Source Repository."""

  detailed_help = {
      'EXAMPLES':
          """\
            To create a push trigger for all branches:

              $ {command} --name="my-trigger" --service-account="projects/my-project/serviceAccounts/my-byosa@my-project.iam.gserviceaccount.com" --repo="my-repo" --branch-pattern=".*" --build-config="cloudbuild.yaml"
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """

    flag_config = trigger_utils.AddTriggerArgs(parser)
    repo_spec = presentation_specs.ResourcePresentationSpec(
        '--repo',  # This defines how the "anchor" or leaf argument is named.
        repo_resource.GetRepoResourceSpec(),
        'Cloud Source Repository.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([repo_spec]).AddToParser(flag_config)
    ref_config = flag_config.add_mutually_exclusive_group(required=True)
    trigger_utils.AddBranchPattern(ref_config)
    trigger_utils.AddTagPattern(ref_config)

    trigger_utils.AddBuildConfigArgs(flag_config)
    trigger_utils.AddRepoEventArgs(flag_config)

  def ParseTriggerFromFlags(self, args):
    """Parses command line arguments into a build trigger.

    Args:
      args: An argparse arguments object.

    Returns:
      A build trigger object.
    """
    messages = cloudbuild_util.GetMessagesModule()

    trigger, done = trigger_utils.ParseTriggerArgs(args, messages)
    if done:
      return trigger

    repo_ref = args.CONCEPTS.repo.Parse()
    repo = repo_ref.reposId
    trigger = messages.BuildTrigger(
        name=args.name,
        description=args.description,
        serviceAccount=args.service_account,
        triggerTemplate=messages.RepoSource(
            repoName=repo,
            branchName=args.branch_pattern,
            tagName=args.tag_pattern,
        ),
    )
    trigger_utils.ParseRequireApproval(trigger, args, messages)

    # Build Config
    project = properties.VALUES.core.project.Get(required=True)
    default_image = 'gcr.io/%s/%s:$COMMIT_SHA' % (project, repo)
    trigger_utils.ParseBuildConfigArgs(trigger, args, messages, default_image)
    trigger_utils.ParseRepoEventArgs(trigger, args)

    return trigger

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    messages = cloudbuild_util.GetMessagesModule()
    trigger = self.ParseTriggerFromFlags(args)

    # Send the Create request
    client = cloudbuild_util.GetClientInstance()
    project = properties.VALUES.core.project.Get(required=True)
    regionprop = properties.VALUES.builds.region.Get()
    location = args.region or regionprop or cloudbuild_util.DEFAULT_REGION
    parent = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=project,
        locationsId=location).RelativeName()
    created_trigger = client.projects_locations_triggers.Create(
        messages.CloudbuildProjectsLocationsTriggersCreateRequest(
            parent=parent, buildTrigger=trigger))

    trigger_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.locations.triggers',
        api_version='v1',
        params={
            'projectsId': project,
            'locationsId': location,
            'triggersId': created_trigger.id,
        })
    log.CreatedResource(trigger_resource)

    return created_trigger
