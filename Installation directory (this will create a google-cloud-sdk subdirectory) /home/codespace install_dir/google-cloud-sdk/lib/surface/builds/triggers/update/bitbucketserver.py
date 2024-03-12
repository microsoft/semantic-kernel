# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Update Bitbucket Server trigger command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import trigger_config as trigger_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class UpdateBitbucketServer(base.UpdateCommand):
  """Updates Bitbucket Server trigger used by Cloud Build."""

  detailed_help = {
      'EXAMPLES':
          """\
            To update the branch pattern of the trigger:

              $ {command} my-trigger --branch-pattern=".*"

            To update the build config of the trigger:

              $ {command} my-trigger --build-config="cloudbuild.yaml"

            To update the substitutions of the trigger:
              $ {command} my-trigger --update-substitutions=_REPO_NAME=my-repo,_BRANCH_NAME=master
        """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    concept_parsers.ConceptParser.ForResource(
        'TRIGGER',
        resource_args.GetTriggerResourceSpec(),
        'Build Trigger.', required=True).AddToParser(parser)

    flag_config = trigger_utils.AddTriggerArgs(
        parser, add_region_flag=False, add_name=False)
    flag_config.add_argument(
        '--repo-slug', help='Bitbucket Server repository slug.')
    flag_config.add_argument(
        '--project-key', help='Bitbucket Server project key.')
    flag_config.add_argument(
        '--bitbucket-server-config-resource',
        help='Bitbucket Server config resource name.')
    ref_config = flag_config.add_mutually_exclusive_group()
    trigger_utils.AddBranchPattern(ref_config)
    trigger_utils.AddTagPattern(ref_config)
    pr_config = ref_config.add_argument_group(help='Pull Request settings')
    pr_config.add_argument(
        '--pull-request-pattern',
        metavar='REGEX',
        help="""\
A regular expression specifying which base git branch to match for
pull request events.

This pattern is used as a regular expression search for the base branch (the
branch you are trying to merge into) for pull request updates.
For example, --pull-request-pattern=foo will match "foo", "foobar", and "barfoo".

The syntax of the regular expressions accepted is the syntax accepted by
RE2 and described at https://github.com/google/re2/wiki/Syntax.
""")
    pr_config.add_argument(
        '--comment-control',
        choices={
            'COMMENTS_DISABLED': ("""
Do not require comments on Pull Requests before builds are triggered."""),
            'COMMENTS_ENABLED': ("""
Enforce that repository owners or collaborators must comment on Pull Requests
before builds are triggered."""),
            'COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY': ("""
Enforce that repository owners or collaborators must comment on external
contributors' Pull Requests before builds are triggered."""),
        },
        default='COMMENTS_ENABLED',
        help=("""\
Require a repository collaborator or owner to comment '/gcbrun' on a pull
request before running the build.
"""),
    )

    trigger_utils.AddBuildConfigArgsForUpdate(
        flag_config, has_build_config=True, require_docker_image=True)
    trigger_utils.AddRepoEventArgs(flag_config)

  def ParseTriggerFromFlags(self, args, old_trigger, update_mask):
    """Parses command line arguments into a build trigger.

    Args:
      args: An argparse arguments object.
      old_trigger: The existing trigger to be updated.
      update_mask: The fields to be updated.

    Returns:
      A build trigger object.

    Raises:
      RequiredArgumentException: If comment_control is defined but
      pull_request_pattern isn't.
    """
    messages = cloudbuild_util.GetMessagesModule()

    trigger, done = trigger_utils.ParseTriggerArgsForUpdate(args, messages)
    if done:
      return trigger

    # Bitbucket Server config
    bbs = messages.BitbucketServerTriggerConfig(
        repoSlug=args.repo_slug,
        projectKey=args.project_key,
        bitbucketServerConfigResource=args.bitbucket_server_config_resource)
    if args.pull_request_pattern:
      bbs.pullRequest = messages.PullRequestFilter(
          branch=args.pull_request_pattern)
      if args.comment_control:
        bbs.pullRequest.commentControl = (
            messages.PullRequestFilter.CommentControlValueValuesEnum(
                args.comment_control
            )
        )
    else:
      # Push event
      bbs.push = messages.PushFilter(
          branch=args.branch_pattern, tag=args.tag_pattern
      )
    trigger.bitbucketServerTriggerConfig = bbs

    trigger_utils.ParseBuildConfigArgsForUpdate(
        trigger,
        old_trigger,
        args,
        messages,
        update_mask,
        None,
        has_build_config=True,
    )
    trigger_utils.ParseRepoEventArgs(trigger, args)

    return trigger

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated Bitbucket Server trigger.
    """

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()
    project = properties.VALUES.core.project.Get(required=True)
    regionprop = properties.VALUES.builds.region.Get()
    location = args.region or regionprop or cloudbuild_util.DEFAULT_REGION
    triggerid = args.TRIGGER

    name = resources.REGISTRY.Parse(
        triggerid,
        params={
            'projectsId': project,
            'locationsId': location,
            'triggersId': triggerid,
        },
        collection='cloudbuild.projects.locations.triggers',
    ).RelativeName()

    old_trigger = client.projects_locations_triggers.Get(
        client.MESSAGES_MODULE.CloudbuildProjectsLocationsTriggersGetRequest(
            name=name, triggerId=triggerid
        )
    )

    update_mask = []
    trigger = self.ParseTriggerFromFlags(args, old_trigger, update_mask)

    # Overwrite the substitutions.additionalProperties in updateMask.
    sub = 'substitutions'
    update_mask.extend(cloudbuild_util.MessageToFieldPaths(trigger))
    update_mask = sorted(
        set(map(lambda m: sub if m.startswith(sub) else m, update_mask))
    )

    req = messages.CloudbuildProjectsLocationsTriggersPatchRequest(
        resourceName=name,
        triggerId=triggerid,
        buildTrigger=trigger,
        updateMask=','.join(update_mask),
    )

    updated_trigger = client.projects_locations_triggers.Patch(req)
    log.UpdatedResource(triggerid, kind='build_trigger')

    return updated_trigger
