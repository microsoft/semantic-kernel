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
"""Set up flags for creating triggers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.builds import flags as build_flags

_CREATE_FILE_DESC = ('A file that contains the configuration for the '
                     'WorkerPool to be created.')
_UPDATE_FILE_DESC = ('A file that contains updates to the configuration for '
                     'the WorkerPool.')


def AddTriggerArgs(parser, add_region_flag=True, add_name=True):
  """Set up the generic argparse flags for creating or updating a build trigger.

  Args:
    parser: An argparse.ArgumentParser-like object.
    add_region_flag: If true, the default region flag is added.
    add_name: If true, the trigger name is added.

  Returns:
    An empty parser group to be populated with flags specific to a trigger-type.
  """

  parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            status
          )
        """)

  trigger_config = parser.add_mutually_exclusive_group(required=True)

  AddTriggerConfigFilePathArg(trigger_config)

  # Trigger configuration
  flag_config = trigger_config.add_argument_group(
      help='Flag based trigger configuration')
  if add_region_flag:
    build_flags.AddRegionFlag(flag_config, hidden=False, required=False)
  AddFlagConfigArgs(flag_config, add_name)

  return flag_config


def AddGitLabEnterpriseTriggerArgs(parser):
  """Set up the generic argparse flags for creating or updating a build trigger for GitLab Enterprise.

  Args:
    parser: An argparse.ArgumentParser-like object.

  Returns:
    An empty parser group to be populated with flags specific to a trigger-type.
  """

  parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            status
          )
        """)

  trigger_config = parser.add_mutually_exclusive_group(required=True)

  AddTriggerConfigFilePathArg(trigger_config)

  # Trigger configuration
  flag_config = trigger_config.add_argument_group(
      help='Flag based trigger configuration')
  build_flags.AddRegionFlag(flag_config, hidden=False, required=False)
  AddFlagConfigArgs(flag_config)

  return flag_config


def AddFlagConfigArgs(flag_config, add_name=True):
  """Adds additional argparse flags related to flag config.

  Args:
    flag_config: Argparse argument group. Additional flags will be added to this
      group to cover common flag configuration settings.
    add_name: If true, the trigger name is added.
  """

  if add_name:
    flag_config.add_argument('--name', help='Build trigger name.')
  flag_config.add_argument('--description', help='Build trigger description.')
  flag_config.add_argument(
      '--service-account',
      help=(
          'The service account used for all user-controlled operations '
          'including UpdateBuildTrigger, RunBuildTrigger, CreateBuild, and '
          'CancelBuild. If no service account is set, then the standard Cloud '
          'Build service account ([PROJECT_NUM]@system.gserviceaccount.com) is '
          'used instead. Format: '
          '`projects/{PROJECT_ID}/serviceAccounts/{ACCOUNT_ID_OR_EMAIL}`.'),
      required=False)
  flag_config.add_argument(
      '--require-approval',
      help='Require manual approval for triggered builds.',
      action=arg_parsers.StoreTrueFalseAction)


def AddTriggerConfigFilePathArg(trigger_config):
  """Allow trigger config to be specified on the command line or STDIN.

  Args:
    trigger_config: the config of which the file path can be specified.
  """

  trigger_config.add_argument(
      '--trigger-config',
      help=("""\
Path to Build Trigger config file (JSON or YAML format). For more details, see
https://cloud.google.com/cloud-build/docs/api/reference/rest/v1/projects.triggers#BuildTrigger
"""),
      metavar='PATH',
  )


def ParseTriggerArgs(args, messages):
  """Parses flags generic to all triggers.

  Args:
    args: An argparse arguments object.
    messages: A Cloud Build messages module

  Returns:
    A partially populated build trigger and a boolean indicating whether or not
    the full trigger was loaded from a file.
  """
  if args.trigger_config:
    trigger = cloudbuild_util.LoadMessageFromPath(
        path=args.trigger_config,
        msg_type=messages.BuildTrigger,
        msg_friendly_name='build trigger config',
        skip_camel_case=['substitutions'])
    return trigger, True

  trigger = messages.BuildTrigger()
  trigger.name = args.name
  trigger.description = args.description
  trigger.serviceAccount = args.service_account
  ParseRequireApproval(trigger, args, messages)
  return trigger, False


def ParseTriggerArgsForUpdate(trigger_args, messages):
  """Parses flags generic to all triggers.

  Args:
    trigger_args: An argparse arguments object.
    messages: A Cloud Build messages module

  Returns:
    A partially populated build trigger and a boolean indicating whether or not
    the full trigger was loaded from a file.
  """
  if trigger_args.trigger_config:
    trigger = cloudbuild_util.LoadMessageFromPath(
        path=trigger_args.trigger_config,
        msg_type=messages.BuildTrigger,
        msg_friendly_name='build trigger config',
        skip_camel_case=['substitutions'])
    return trigger, True

  trigger = messages.BuildTrigger()
  trigger.description = trigger_args.description
  trigger.serviceAccount = trigger_args.service_account
  ParseRequireApproval(trigger, trigger_args, messages)
  return trigger, False


def AddIncludeLogsArgs(flag_config):
  """Add flag related to including logs for GitHub checkrun summary page.

  Args:
    flag_config: argparse argument group. Include logs for GitHub will be
    added to this config.
  """

  flag_config.add_argument(
      '--include-logs-with-status',
      help=(
          'Build logs will be sent back to GitHub as part of the checkrun '
          'result.'
      ), action='store_true')


def AddRepoEventArgs(flag_config):
  """Adds additional argparse flags related to repo events.

  Args:
    flag_config: argparse argument group. Additional flags will be added to this
      group to cover common build configuration settings.
  """

  flag_config.add_argument(
      '--included-files',
      help=("""\
Glob filter. Changes affecting at least one included file will trigger builds.
"""),
      type=arg_parsers.ArgList(),
      metavar='GLOB',
  )
  flag_config.add_argument(
      '--ignored-files',
      help=("""\
Glob filter. Changes only affecting ignored files won't trigger builds.
"""),
      type=arg_parsers.ArgList(),
      metavar='GLOB',
  )


def AddFilterArg(flag_config):
  """Adds trigger filter flag arg.

  Args:
    flag_config: argparse argument group. Trigger filter flag will be added to
      this config.
  """
  flag_config.add_argument(
      '--subscription-filter',
      help=("""\
CEL filter expression for the trigger. See https://cloud.google.com/build/docs/filter-build-events-using-cel for more details.
"""),
  )


def AddFilterArgForUpdate(flag_config):
  """Adds trigger filter flag arg.

  Args:
    flag_config: argparse argument group. Trigger filter flag will be added to
      this config.
  """
  filter_arg = flag_config.add_mutually_exclusive_group()
  filter_arg.add_argument(
      '--subscription-filter',
      default=None,
      help=("""\
CEL filter expression for the trigger. See https://cloud.google.com/build/docs/filter-build-events-using-cel for more details.
"""),
  )
  filter_arg.add_argument(
      '--clear-subscription-filter',
      action='store_true',
      help='Clear existing subscription filter.',
  )


def AddSubstitutions(argument_group):
  """Adds a substituion flag to the given argument group.

  Args:
    argument_group: argparse argument group to which the substitution flag will
      be added.
  """

  argument_group.add_argument(
      '--substitutions',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
Parameters to be substituted in the build specification. For example:

  $ {command} ... --substitutions _FAVORITE_COLOR=blue,_NUM_CANDIES=10

This will result in a build where every occurrence of ```${_FAVORITE_COLOR}```
in certain fields is replaced by "blue", and similarly for ```${_NUM_CANDIES}```
and "10".

Substitutions can be applied to user-defined variables (starting with an
underscore) and to the following built-in variables: REPO_NAME, BRANCH_NAME,
TAG_NAME, REVISION_ID, COMMIT_SHA, SHORT_SHA.

For more details, see:
https://cloud.google.com/build/docs/configuring-builds/substitute-variable-values
""")


def AddSubstitutionUpdatingFlags(argument_group):
  """Adds substitution updating flags to the given argument group.

  Args:
    argument_group: argparse argument group to which the substitution updating
      flags flag will be added.
  """

  argument_group.add_argument(
      '--update-substitutions',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
Update or add to existing substitutions.
Substitutions are parameters to be substituted or add in the build specification.

For example (using some nonsensical substitution keys; all keys must begin with
an underscore):

  $ gcloud builds triggers update ...
      --update-substitutions _FAVORITE_COLOR=blue,_NUM_CANDIES=10

This will add the provided substitutions to the existing substitutions and
results in a build where every occurrence of ```${_FAVORITE_COLOR}```
in certain fields is replaced by "blue", and similarly for ```${_NUM_CANDIES}```
and "10".

Only the following built-in variables can be specified with the
`--substitutions` flag: REPO_NAME, BRANCH_NAME, TAG_NAME, REVISION_ID,
COMMIT_SHA, SHORT_SHA.

For more details, see:
https://cloud.google.com/build/docs/build-config-file-schema#substitutions
""",
  )

  argument_group.add_argument(
      '--clear-substitutions',
      action='store_true',
      help='Clear existing substitutions.',
  )

  argument_group.add_argument(
      '--remove-substitutions',
      metavar='KEY',
      type=arg_parsers.ArgList(),
      help='Remove existing substitutions if present.',
  )


def AddBuildConfigArgs(
    flag_config, add_docker_args=True, require_docker_image=False
):
  """Adds additional argparse flags to a group for build configuration options.

  Args:
    flag_config: argparse argument group. Additional flags will be added to this
      group to cover common build configuration settings.
    add_docker_args: If true, docker args are added automatically.
    require_docker_image: If true, --dockerfile-image must be provided.
  Returns:
    build_config: a build config.
  """

  # Build config and inline config support substitutions whereas dockerfile
  # does not. We can't have a flag with the same name in two separate
  # groups so we have to have one flag outside of the config argument group.
  AddSubstitutions(flag_config)

  build_config = flag_config.add_mutually_exclusive_group(required=True)

  build_config.add_argument(
      '--build-config',
      metavar='PATH',
      help="""\
Path to a YAML or JSON file containing the build configuration in the repository.

For more details, see: https://cloud.google.com/cloud-build/docs/build-config
""")

  build_config.add_argument(
      '--inline-config',
      metavar='PATH',
      help="""\
      Local path to a YAML or JSON file containing a build configuration.
    """)

  if add_docker_args:
    AddBuildDockerArgs(build_config, require_docker_image=require_docker_image)
  return build_config


def AddBuildDockerArgs(
    argument_group,
    require_docker_image=False,
    update=False):
  """Adds additional argparse flags to a group for build docker options.

  Args:
    argument_group: argparse argument group to which build docker flag will
      be added.
    require_docker_image: If true, --dockerfile-image must be provided.
    update: Whether the command is update.
  """
  docker = argument_group.add_argument_group(
      help='Dockerfile build configuration flags')
  docker.add_argument(
      '--dockerfile',
      required=True,
      help="""\
Path of Dockerfile to use for builds in the repository.

If specified, a build config will be generated to run docker
build using the specified file.

The filename is relative to the Dockerfile directory.
""")
  default_dir = '/'
  if update:
    default_dir = None
  docker.add_argument(
      '--dockerfile-dir',
      default=default_dir,
      help="""\
Location of the directory containing the Dockerfile in the repository.

The directory will also be used as the Docker build context.
""")

  docker_image_help_text = """\
Docker image name to build.

If not specified, gcr.io/PROJECT/github.com/REPO_OWNER/REPO_NAME:$COMMIT_SHA will be used.

Use a build configuration (cloudbuild.yaml) file for building multiple images in a single trigger.
"""
  if require_docker_image:
    docker_image_help_text = 'Docker image name to build.'
  docker.add_argument(
      '--dockerfile-image',
      required=require_docker_image,
      help=docker_image_help_text)


def AddBuildConfigArgsForUpdate(flag_config,
                                has_build_config=False,
                                has_file_source=False,
                                require_docker_image=False):
  """Adds additional argparse flags to a group for build configuration options for update command.

  Args:
    flag_config: Argparse argument group. Additional flags will be added to this
      group to cover common build configuration settings.
    has_build_config: Whether it is possible for the trigger to have
      filename.
    has_file_source: Whether it is possible for the trigger to have
      git_file_source.
    require_docker_image: If true, dockerfile image must be provided.

  Returns:
    build_config: A build config.
  """

  # Build config and inline config support substitutions whereas Dockerfile
  # does not. Cloud Build cannot have a flag with the same name in two separate
  # groups. You must add a flag outside of the config argument group.
  substitutions = flag_config.add_mutually_exclusive_group()
  AddSubstitutionUpdatingFlags(substitutions)

  build_config = flag_config.add_mutually_exclusive_group()

  if has_build_config:
    build_config.add_argument(
        '--build-config',
        metavar='PATH',
        help="""\
  Path to a YAML or JSON file containing the build configuration in the repository.

  For more details, see: https://cloud.google.com/cloud-build/docs/build-config
  """)

  build_config.add_argument(
      '--inline-config',
      metavar='PATH',
      help="""\
      Local path to a YAML or JSON file containing a build configuration.
    """)

  if has_file_source:
    AddGitFileSourceArgs(build_config)

  AddBuildDockerArgs(
      build_config, require_docker_image=require_docker_image, update=True)

  return build_config


def AddRepoSourceForUpdate(flag_config):
  """Adds additional argparse flags to a group for git repo source options for update commands.

  Args:
    flag_config: Argparse argument group. Git repo source flags will be added to
      this group.
  """
  source_to_build = flag_config.add_mutually_exclusive_group()
  source_to_build.add_argument(
      '--source-to-build-repository',
      hidden=True,
      help="""\
Repository resource (2nd gen) to use, in the format "projects/*/locations/*/connections/*/repositories/*".
""")
  v1_gen_source = source_to_build.add_argument_group()
  v1_gen_source.add_argument(
      '--source-to-build-github-enterprise-config',
      help="""\
The resource name of the GitHub Enterprise config that should be applied to
this source (1st gen).
Format: projects/{project}/locations/{location}/githubEnterpriseConfigs/{id}
or projects/{project}/githubEnterpriseConfigs/{id}
""")
  v1_gen_repo_info = v1_gen_source.add_argument_group()
  v1_gen_repo_info.add_argument(
      '--source-to-build-repo-type',
      required=True,
      help="""\
Type of the repository (1st gen). Currently only GitHub and Cloud Source
Repository types are supported.
""")
  v1_gen_repo_info.add_argument(
      '--source-to-build-uri',
      required=True,
      help="""\
The URI of the repository that should be applied to this source (1st gen).
""")

  ref_config = flag_config.add_mutually_exclusive_group()
  ref_config.add_argument('--source-to-build-branch', help='Branch to build.')
  ref_config.add_argument('--source-to-build-tag', help='Tag to build.')


def AddGitFileSourceArgs(argument_group):
  """Adds additional argparse flags to a group for git file source options.

  Args:
    argument_group: Argparse argument group to which git file source flag will
      be added.
  """

  git_file_source = argument_group.add_argument_group(
      help='Build file source flags')
  repo_source = git_file_source.add_mutually_exclusive_group()
  repo_source.add_argument(
      '--git-file-source-repository',
      hidden=True,
      help="""\
Repository resource (2nd gen) to use, in the format "projects/*/locations/*/connections/*/repositories/*".
""")
  v1_gen_source = repo_source.add_argument_group()
  v1_gen_source.add_argument(
      '--git-file-source-path',
      metavar='PATH',
      help="""\
The file in the repository to clone when trigger is invoked.
""")
  v1_gen_repo_info = v1_gen_source.add_argument_group()
  v1_gen_repo_info.add_argument(
      '--git-file-source-uri',
      required=True,
      metavar='URL',
      help="""\
The URI of the repository to clone when trigger is invoked.
""")
  v1_gen_repo_info.add_argument(
      '--git-file-source-repo-type',
      required=True,
      help="""\
The type of the repository to clone when trigger is invoked.
""")
  v1_gen_source.add_argument(
      '--git-file-source-github-enterprise-config',
      help="""\
The resource name of the GitHub Enterprise config that should be applied to this source.
""")
  ref_config = git_file_source.add_mutually_exclusive_group()
  ref_config.add_argument(
      '--git-file-source-branch',
      help="""\
The branch of the repository to clone when trigger is invoked.
""")
  ref_config.add_argument(
      '--git-file-source-tag',
      help="""\
The tag of the repository to clone when trigger is invoked.
""")


def AddCommentControlArg(argument_group):
  """Adds additional argparse flags to a group for comment control options.

  Args:
    argument_group: Argparse argument group to which comment control flag will
      be added.
  """
  argument_group.add_argument(
      '--comment-control',
      default='COMMENTS_ENABLED',
      help=(
          "Require a repository collaborator or owner to comment '/gcbrun' on"
          ' a pull request before running the build.'
      ),
      choices={
          'COMMENTS_DISABLED': (
              'Do not require comments on Pull Requests before builds are'
              ' triggered.'
          ),
          'COMMENTS_ENABLED': (
              'Enforce that repository owners or collaborators must comment'
              ' on Pull Requests before builds are triggered.'
          ),
          'COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY': (
              'Enforce that repository owners or collaborators must comment'
              " on external contributors' Pull Requests before builds are"
              ' triggered.'
          ),
      },
  )


def ParseRepoEventArgs(trigger, args):
  """Parses repo event related flags.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
  """
  if args.included_files:
    trigger.includedFiles = args.included_files
  if args.ignored_files:
    trigger.ignoredFiles = args.ignored_files


def ParseBuildConfigArgs(trigger,
                         args,
                         messages,
                         default_image,
                         need_repo=False):
  """Parses build-config flags.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
    default_image: The docker image to use if args.dockerfile_image is empty.
    need_repo: Whether or not a repo needs to be included explicitly in flags.
  """
  if args.build_config:
    # If we don't need a repo, then the repository information is already known
    # and we just need the filename. Otherwise, this trigger needs to
    # be a GitFileSource trigger (which is taken care of in ParseGitRepoSource).
    if not need_repo:
      trigger.filename = args.build_config
    trigger.substitutions = cloudbuild_util.EncodeTriggerSubstitutions(
        args.substitutions, messages.BuildTrigger.SubstitutionsValue)
  if args.dockerfile:

    if args.substitutions:
      raise c_exceptions.ConflictingArgumentsException(
          'Dockerfile and substitutions',
          'Substitutions are not supported with a Dockerfile configuration.')

    image = args.dockerfile_image or default_image
    trigger.build = messages.Build(steps=[
        messages.BuildStep(
            name='gcr.io/cloud-builders/docker',
            dir=args.dockerfile_dir,
            args=['build', '-t', image, '-f', args.dockerfile, '.'],
        )
    ])
  if args.inline_config:
    trigger.build = cloudbuild_util.LoadMessageFromPath(args.inline_config,
                                                        messages.Build,
                                                        'inline build config',
                                                        ['substitutions'])
    trigger.substitutions = cloudbuild_util.EncodeTriggerSubstitutions(
        args.substitutions, messages.BuildTrigger.SubstitutionsValue)

  if need_repo:
    # Repo is required if a build config (filename) or dockerfile was provided.
    required = args.build_config or args.dockerfile
    ParseGitRepoSource(trigger, args, messages, required=required)


def ParseBuildConfigArgsForUpdate(trigger,
                                  old_trigger,
                                  args,
                                  messages,
                                  update_mask,
                                  default_image,
                                  has_build_config=False,
                                  has_repo_source=False,
                                  has_file_source=False):
  """Parses build-config flags for update command.

  Args:
    trigger: The trigger to populate.
    old_trigger: The existing trigger to be updated.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
    update_mask: The fields to be updated.
    default_image: The default docker image to use.
    has_build_config: Whether it is possible for the trigger to have
      filename.
    has_repo_source: Whether it is possible for the trigger to have
      source_to_build.
    has_file_source: Whether it is possible for the trigger to have
      git_file_source.
  """
  if has_build_config:
    trigger.filename = args.build_config

  if args.dockerfile:
    if args.update_substitutions:
      raise c_exceptions.ConflictingArgumentsException(
          'Dockerfile and substitutions',
          'Substitutions are not supported with a Dockerfile configuration.')

    if args.dockerfile_dir:
      dockerfile_dir = args.dockerfile_dir
    elif old_trigger.build and old_trigger.build.steps:
      dockerfile_dir = old_trigger.build.steps[0].dir
    else:
      dockerfile_dir = '/'

    dockerfile_image = args.dockerfile_image or default_image
    trigger.build = messages.Build(steps=[
        messages.BuildStep(
            name='gcr.io/cloud-builders/docker',
            dir=dockerfile_dir,
            args=[
                'build', '-t', dockerfile_image, '-f', args.dockerfile, '.'
            ],
        )
    ])
  if args.inline_config:
    trigger.build = cloudbuild_util.LoadMessageFromPath(args.inline_config,
                                                        messages.Build,
                                                        'inline build config',
                                                        ['substitutions'])

  if args.update_substitutions:
    trigger.substitutions = cloudbuild_util.EncodeUpdatedTriggerSubstitutions(
        old_trigger.substitutions, args.update_substitutions, messages)

  if args.clear_substitutions:
    trigger.substitutions = cloudbuild_util.EncodeEmptyTriggerSubstitutions(
        messages)

  if args.remove_substitutions:
    trigger.substitutions = cloudbuild_util.RemoveTriggerSubstitutions(
        old_trigger.substitutions, args.remove_substitutions, messages
    )

  if has_repo_source and (
      args.source_to_build_uri
      or args.source_to_build_branch
      or args.source_to_build_tag
      or args.source_to_build_repo_type
      or args.source_to_build_github_enterprise_config
      or args.source_to_build_repository
  ):
    ParseGitRepoSourceForUpdate(trigger, args, messages, update_mask)

  if has_file_source and (
      args.git_file_source_uri or args.git_file_source_path or
      args.git_file_source_repo_type or
      args.git_file_source_branch or args.git_file_source_tag or
      args.git_file_source_github_enterprise_config or
      args.git_file_source_repository):
    ParseGitFileSource(trigger, args, messages, update_mask)


def ParseGitRepoSourceForUpdate(trigger, args, messages, update_mask):
  """Parses git repo source flags for update command.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
    update_mask: The fields to be updated.
  """

  trigger.sourceToBuild = messages.GitRepoSource()
  reporef = None
  if args.source_to_build_branch:
    reporef = 'refs/heads/' + args.source_to_build_branch
  elif args.source_to_build_tag:
    reporef = 'refs/tags/' + args.source_to_build_tag
  if reporef:
    trigger.sourceToBuild.ref = reporef

  if args.source_to_build_repository:
    trigger.sourceToBuild.repository = args.source_to_build_repository
    # Clear the 1st-gen repo info when updating 2nd-gen repo resource.
    update_mask.append('source_to_build.uri')
    update_mask.append('source_to_build.repo_type')
    update_mask.append('source_to_build.github_enterprise_config')
  elif (
      args.source_to_build_uri
      or args.source_to_build_github_enterprise_config
      or args.source_to_build_repo_type
  ):
    trigger.sourceToBuild.uri = args.source_to_build_uri
    trigger.sourceToBuild.githubEnterpriseConfig = (
        args.source_to_build_github_enterprise_config
    )
    if args.source_to_build_repo_type:
      trigger.sourceToBuild.repoType = (
          messages.GitRepoSource.RepoTypeValueValuesEnum(
              args.source_to_build_repo_type
          )
      )
    # Clear the 2nd-gen repo info when updating 1st-gen repo resource.
    update_mask.append('source_to_build.repository')


def ParseGitFileSource(trigger, args, messages, update_mask):
  """Parses git repo source flags.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
    update_mask: The fields to be updated.
  """

  trigger.gitFileSource = messages.GitFileSource()
  revision = None
  if args.git_file_source_branch:
    revision = 'refs/heads/' + args.git_file_source_branch
  elif args.git_file_source_tag:
    revision = 'refs/tags/' + args.git_file_source_tag
  trigger.gitFileSource.revision = revision

  if args.git_file_source_repository:
    trigger.gitFileSource.repository = args.git_file_source_repository
    # Clear the 1st-gen repo info when updating 2nd-gen repo resource.
    update_mask.append('git_file_source.uri')
    update_mask.append('git_file_source.repo_type')
    update_mask.append('git_file_source.github_enterprise_config')
    update_mask.append('git_file_source.path')
  elif (
      args.git_file_source_github_enterprise_config
      or args.git_file_source_uri
      or args.git_file_source_path
      or args.git_file_source_repo_type
  ):
    trigger.gitFileSource.path = args.git_file_source_path
    trigger.gitFileSource.uri = args.git_file_source_uri
    trigger.gitFileSource.githubEnterpriseConfig = (
        args.git_file_source_github_enterprise_config
    )
    if args.git_file_source_repo_type:
      trigger.gitFileSource.repoType = (
          messages.GitFileSource.RepoTypeValueValuesEnum(
              args.git_file_source_repo_type
          )
      )
    # Clear the 2nd-gen repo info when updating 1st-gen repo resource.
    update_mask.append('git_file_source.repository')


def AddBranchPattern(parser):
  parser.add_argument(
      '--branch-pattern',
      metavar='REGEX',
      help="""\
A regular expression specifying which git branches to match.

This pattern is used as a regular expression search for any incoming pushes.
For example, --branch-pattern=foo will match "foo", "foobar", and "barfoo".
Events on a branch that does not match will be ignored.

The syntax of the regular expressions accepted is the syntax accepted by
RE2 and described at https://github.com/google/re2/wiki/Syntax.
""")


def AddTagPattern(parser):
  parser.add_argument(
      '--tag-pattern',
      metavar='REGEX',
      help="""\
A regular expression specifying which git tags to match.

This pattern is used as a regular expression search for any incoming pushes.
For example, --tag-pattern=foo will match "foo", "foobar", and "barfoo".
Events on a tag that does not match will be ignored.

The syntax of the regular expressions accepted is the syntax accepted by
RE2 and described at https://github.com/google/re2/wiki/Syntax.
""")


def AddGitRepoSource(flag_config):
  """Adds additional argparse flags to a group for git repo source options.

  Args:
    flag_config: argparse argument group. Git repo source flags will be added to
      this group.
  """
  repo_config = flag_config.add_argument_group(
      help='Flags for repository and branch information')
  gen_config = repo_config.add_mutually_exclusive_group(
      help='Flags for repository information')
  gen_config.add_argument(
      '--repository',
      help="""\
Repository resource (2nd gen) to use, in the format "projects/*/locations/*/connections/*/repositories/*".
""")
  v1_repo = gen_config.add_argument_group(help='1st-gen repository settings.')
  v1_repo.add_argument(
      '--repo',
      required=True,
      help=("""\
URI of the repository (1st gen). Currently only HTTP URIs for GitHub and Cloud
Source Repositories are supported.
"""),
  )
  v1_repo.add_argument(
      '--repo-type',
      required=True,
      help=("""\
Type of the repository (1st gen). Currently only GitHub and Cloud Source Repository types
are supported.
"""),
  )
  config = v1_repo.add_mutually_exclusive_group()
  config.add_argument(
      '--github-enterprise-config',
      help="""\
The resource name of the GitHub Enterprise config that should be applied to this source (1st gen).
Format: projects/{project}/locations/{location}/githubEnterpriseConfigs/{id} or projects/{project}/githubEnterpriseConfigs/{id}
""")
  config.add_argument(
      '--bitbucket-server-config',
      hidden=True,
      help="""\
The resource name of the Bitbucket Server config that should be applied to this source (1st gen).
Format: projects/{project}/locations/{location}/bitbucketServerConfigs/{id}
""")

  ref_config = repo_config.add_mutually_exclusive_group()
  ref_config.add_argument('--branch', help='Branch to build.')
  ref_config.add_argument('--tag', help='Tag to build.')


def ParseGitRepoSource(trigger, args, messages, required=False):
  """Parses git repo source flags.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
    required: Whether or not the repository info is required.
  """

  # AddGitRepoSource (defined earlier in this file) adds repo/repository and
  # branch/tag as required fields in the same argument group, so repo is set
  # iff branch or tag is also set. Therefore, we only need to check for the
  # presence of args.repo or args.repository here.
  if required and not args.repo and not args.repository:
    raise c_exceptions.RequiredArgumentException(
        'REPO',
        (
            '--repo or --repository is required when specifying a --dockerfile'
            ' or --build-config.'
        ),
    )

  # Repoless trigger.
  if not args.repo and not args.repository:
    if args.branch or args.tag:
      raise c_exceptions.RequiredArgumentException(
          'REPO',
          (
              '--repo or --repository is required when specifying a'
              ' --branch or --tag.'
          ),
      )
    return

  if not args.branch and not args.tag:
    raise c_exceptions.RequiredArgumentException(
        'REVISION',
        '--branch or --tag is required when specifying a --repository'
        ' or --repo.',
    )

  if args.branch:
    ref = 'refs/heads/' + args.branch
  else:
    ref = 'refs/tags/' + args.tag

  parsed_git_repo_source_repo_type = (
      None if not args.repo_type
      else messages.GitRepoSource.RepoTypeValueValuesEnum(args.repo_type)
  )

  trigger.sourceToBuild = messages.GitRepoSource(
      repository=args.repository,
      uri=args.repo,
      ref=ref,
      repoType=parsed_git_repo_source_repo_type,
      githubEnterpriseConfig=args.github_enterprise_config,
      bitbucketServerConfig=args.bitbucket_server_config,
  )

  parsed_git_file_source_repo_type = (
      None if not args.repo_type
      else messages.GitFileSource.RepoTypeValueValuesEnum(args.repo_type)
  )

  if args.build_config:
    trigger.gitFileSource = messages.GitFileSource(
        repository=args.repository,
        path=args.build_config,
        uri=args.repo,
        revision=ref,
        repoType=parsed_git_file_source_repo_type,
        githubEnterpriseConfig=args.github_enterprise_config,
        bitbucketServerConfig=args.bitbucket_server_config)


def ParseRequireApproval(trigger, args, messages):
  """Parses approval required flag.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
  """

  if args.require_approval is not None:
    trigger.approvalConfig = messages.ApprovalConfig(
        approvalRequired=args.require_approval
    )


def ParseIncludeLogsWithStatus(trigger, args, messages):
  """Parses include logs with status flag.

  Args:
    trigger: The trigger to populate.
    args: An argparse arguments object.
    messages: A Cloud Build messages module.
  """

  if args.include_logs_with_status:
    trigger.includeBuildLogs = (
        messages.BuildTrigger
        .IncludeBuildLogsValueValuesEnum.INCLUDE_BUILD_LOGS_WITH_STATUS)
