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
"""Submit build command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.command_lib.builds import submit_util


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.

  Returns:
    worker pool flag group
  """
  source = parser.add_mutually_exclusive_group()
  source.add_argument(
      'source',
      nargs='?',
      default='.',  # By default, the current directory is used.
      help=(
          'The location of the source to build. The location can be a directory'
          ' on a local disk, a gzipped archive file (.tar.gz) in Google Cloud'
          ' Storage, or a Git repo url starting with http:// or https://. If'
          ' the source is a local directory, this command skips the files'
          ' specified in the `--ignore-file`. If `--ignore-file` is not'
          ' specified, use`.gcloudignore` file. If a `.gcloudignore` file is'
          ' absent and a `.gitignore` file is present in the local source'
          ' directory, gcloud will use a generated Git-compatible'
          ' `.gcloudignore` file that respects your .gitignored files. The'
          ' global `.gitignore` is not respected. For more information on'
          ' `.gcloudignore`, see `gcloud topic gcloudignore`.'
      ),
  )
  source.add_argument(
      '--no-source',
      action='store_true',
      help='Specify that no source should be uploaded with this build.',
  )

  flags.AddRegionFlag(parser)
  flags.AddGcsSourceStagingDirFlag(parser)
  flags.AddGcsLogDirFlag(parser)
  flags.AddTimeoutFlag(parser)

  flags.AddMachineTypeFlag(parser)
  flags.AddDiskSizeFlag(parser)
  flags.AddSubstitutionsFlag(parser)
  flags.AddDefaultBucketsBehaviorFlag(parser)
  worker_pools = flags.AddWorkerPoolFlag(parser)

  flags.AddNoCacheFlag(parser)
  flags.AddAsyncFlag(parser)
  flags.AddSuppressLogsFlag(parser)
  parser.display_info.AddFormat("""
        table(
          id,
          createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
          duration(start=startTime,end=finishTime,precision=0,calendar=false,undefined="  -").slice(2:).join(""):label=DURATION,
          build_source(undefined="-"):label=SOURCE,
          build_images(undefined="-"):label=IMAGES,
          status
        )
      """)
  # Do not try to create a URI to update the cache.
  parser.display_info.AddCacheUpdater(None)

  flags.AddIgnoreFileFlag(parser)
  flags.AddConfigFlags(parser)

  parser.add_argument(
      '--git-source-dir',
      help="""\
Directory, relative to the source root, in which to run the build.
This must be a relative path. If a step's `dir` is specified and is an absolute
path, this value is ignored for that step's execution.
""",
  )
  parser.add_argument(
      '--git-source-revision',
      help="""\
Revision to fetch from the Git repository such as a branch, a tag, a commit
SHA, or any Git ref to run the build.

Cloud Build uses `git fetch` to fetch the revision from the Git repository;
therefore make sure that the string you provide for `revision` is parsable by
the command. For information on string values accepted by `git fetch`, see
https://git-scm.com/docs/gitrevisions#_specifying_revisions. For information on
`git fetch`, see https://git-scm.com/docs/git-fetch.
""",
  )
  parser.add_argument(
      '--dir',
      help="""\
Directory, relative to the source root, in which to run the build. This is used when the build source is a 2nd-gen Cloud Build repository resource.
This must be a relative path. If a step's `dir` is specified and is an absolute
path, this value is ignored for that step's execution.
""",
  )
  parser.add_argument(
      '--revision',
      help="""\
Revision to fetch from the Git repository such as a branch, a tag, a commit
SHA, or any Git ref to run the build. This is used when the build source is a 2nd-gen Cloud Build repository resource.

Cloud Build uses `git fetch` to fetch the revision from the Git repository;
therefore make sure that the string you provide for `revision` is parsable by
the command. For information on string values accepted by `git fetch`, see
https://git-scm.com/docs/gitrevisions#_specifying_revisions. For information on
`git fetch`, see https://git-scm.com/docs/git-fetch.
""",
  )

  return worker_pools


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Submit(base.CreateCommand):
  """Submit a build using Cloud Build.

  Submit a build using Cloud Build.
  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          When the `builds/use_kaniko` property is `True`, builds submitted with
          `--tag` will use Kaniko
          (https://github.com/GoogleContainerTools/kaniko) to execute builds.
          Kaniko executes directives in a Dockerfile, with remote layer caching
          for faster builds. By default, Kaniko will cache layers for 6 hours.
          To override this, set the `builds/kaniko_cache_ttl` property.
      """,
      'EXAMPLES': """
      To submit a build with source located at storage URL `gs://bucket/object.zip`:

         $ {command}  "gs://bucket/object.zip" --tag=gcr.io/my-project/image

      To submit a build with source located at storage URL `gs://bucket/object.zip`
      using config file `config.yaml`:

        $ {command} "gs://bucket/object.zip" --tag=gcr.io/my-project/image --config=config.yaml

      To submit a build with local source `source.tgz` asynchronously:

        $ {command} "source.tgz" --tag=gcr.io/my-project/image --async

      To submit a build with source from a Git repository `https://github.com/owner/repo`:

        $ {command} "https://github.com/owner/repo" --git-source-revision=main --config=config.yaml

      To submit a build with source from a 2nd-gen Cloud Build repository resource `projects/my-project/locations/us-west1/connections/my-conn/repositories/my-repo`:

        $ {command} "projects/my-project/locations/us-west1/connections/my-conn/repositories/my-repo" --revision=main
      """,
  }

  _support_gcl = False

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedBuildException: If the build is completed and not 'SUCCESS'.
    """
    build_region = args.region

    messages = cloudbuild_util.GetMessagesModule()

    # Create the build request.
    build_config = submit_util.CreateBuildConfig(
        args.tag,
        args.no_cache,
        messages,
        args.substitutions,
        args.config,
        args.IsSpecified('source'),
        args.no_source,
        args.source,
        args.gcs_source_staging_dir,
        args.ignore_file,
        args.gcs_log_dir,
        args.machine_type,
        args.disk_size,
        args.worker_pool,
        args.git_source_dir,
        args.git_source_revision,
        args.dir,
        args.revision,
        args.pack,
        False,
        args.default_buckets_behavior,
        skip_set_source=True,
        client_tag='gcloudsubmits'
    )

    build_region = submit_util.DetermineBuildRegion(build_config, build_region)
    build_region = build_region or cloudbuild_util.DEFAULT_REGION

    # Set build_config source with updated build_region.
    build_config = submit_util.SetSource(
        build_config,
        messages,
        args.IsSpecified('source'),
        args.no_source,
        args.source,
        args.gcs_source_staging_dir,
        args.dir,
        args.revision,
        args.git_source_dir,
        args.git_source_revision,
        args.ignore_file,
        False,
        build_region,
        args.default_buckets_behavior,
    )

    # Start the build.
    build, _ = submit_util.Build(
        messages,
        args.async_,
        build_config,
        build_region=build_region,
        support_gcl=self._support_gcl,
        suppress_logs=args.suppress_logs)
    return build


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SubmitBeta(Submit):
  """Submit a build using Cloud Build.

  Submit a build using Cloud Build.
  """

  _support_gcl = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SubmitAlpha(SubmitBeta):
  """Submit a build using Cloud Build.

  Submit a build using Cloud Build.
  """

  @staticmethod
  def Args(parser):
    worker_pools = _CommonArgs(parser)
    flags.AddConfigFlagsAlpha(worker_pools)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedBuildException: If the build is completed and not 'SUCCESS'.
    """
    build_region = args.region

    messages = cloudbuild_util.GetMessagesModule()

    # Create the build request.
    build_config = submit_util.CreateBuildConfigAlpha(
        args.tag,
        args.no_cache,
        messages,
        args.substitutions,
        args.config,
        args.IsSpecified('source'),
        args.no_source,
        args.source,
        args.gcs_source_staging_dir,
        args.ignore_file,
        args.gcs_log_dir,
        args.machine_type,
        args.disk_size,
        args.memory,
        args.vcpu_count,
        args.worker_pool,
        args.dir,
        args.revision,
        args.git_source_dir,
        args.git_source_revision,
        args.pack,
        False,
        args.default_buckets_behavior,
        skip_set_source=True,
        client_tag='gcloudsubmits'
    )

    build_region = submit_util.DetermineBuildRegion(build_config, build_region)
    build_region = build_region or cloudbuild_util.DEFAULT_REGION

    # Set build_config source with updated build_region.
    build_config = submit_util.SetSource(
        build_config,
        messages,
        args.IsSpecified('source'),
        args.no_source,
        args.source,
        args.gcs_source_staging_dir,
        args.dir,
        args.revision,
        args.git_source_dir,
        args.git_source_revision,
        args.ignore_file,
        False,
        build_region,
        args.default_buckets_behavior,
    )

    # Start the build.
    build, _ = submit_util.Build(
        messages,
        args.async_,
        build_config,
        build_region=build_region,
        support_gcl=True)
    return build
