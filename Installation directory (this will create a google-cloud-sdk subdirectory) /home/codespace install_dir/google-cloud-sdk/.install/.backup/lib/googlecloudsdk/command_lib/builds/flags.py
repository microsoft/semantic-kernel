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

"""Flags and helpers for the builds command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties
import six

_machine_type_flag_map = None


class BuildsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BuildsCompleter, self).__init__(
        collection='cloudbuild.projects.builds',
        list_command='builds list --uri',
        **kwargs)


def AddRegionFlag(parser, hidden=False, required=False):
  """Adds a flag to select a region of the Cloud Build Service.

  Args:
    parser: The argparse parser to add the arg to.
    hidden: If true, retain help but do not display it.
    required: If true, the field must be set or will raise an exception.
  """
  parser.add_argument(
      '--region',
      hidden=hidden,
      required=required,
      help='The region of the Cloud Build Service to use.\n'
      'Must be set to a supported region name (e.g. `us-central1`).\n'
      'If unset, `builds/region`, which is the default region to use when '
      'working with Cloud Build resources, is used. If builds/region is unset, '
      'region is set to `global`.\n'
      'Note: Region must be specified in 2nd gen repo; '
      '`global` is not supported.')


def AddBuildArg(parser, intro=None):
  """Adds a 'build' arg to the given parser.

  Args:
    parser: The argparse parser to add the arg to.
    intro: Introductory sentence.
  """
  if intro:
    help_text = intro + ' '
  else:
    help_text = ''
  help_text += ('The ID of the build is printed at the end of the build '
                'submission process, or in the ID column when listing builds.')
  parser.add_argument(
      'build',
      completer=BuildsCompleter,
      help=help_text)


def AddNoCacheFlag(parser, hidden=False):
  """Add a flag to disable layer caching."""
  parser.add_argument(
      '--no-cache',
      hidden=hidden,
      action='store_true',
      help='If set, disable layer caching when building with Kaniko.\n'
      '\n'
      'This has the same effect as setting the builds/kaniko_cache_ttl '
      'property to 0 for this build.  This can be useful in cases where '
      'Dockerfile builds are non-deterministic and a non-deterministic '
      'result should not be cached.')


def AddDiskSizeFlag(parser, hidden=False):
  """Add a disk size flag."""
  parser.add_argument(
      '--disk-size',
      hidden=hidden,
      type=arg_parsers.BinarySize(lower_bound='100GB', upper_bound='1TB'),
      help='Machine disk size (GB) to run the build.')


def AddGcsLogDirFlag(parser, hidden=False):
  """Add a GCS directory flag to hold build logs."""
  parser.add_argument(
      '--gcs-log-dir',
      hidden=hidden,
      help=(
          'A directory in Google Cloud Storage to hold build logs. If this'
          ' field is not set,'
          ' ```gs://[PROJECT_NUMBER].cloudbuild-logs.googleusercontent.com/```'
          ' will be created and used or'
          ' ```gs://[PROJECT_NUMBER]-[builds/region]-cloudbuild-logs``` is used'
          ' when you set `--default-buckets-behavior` to'
          ' `REGIONAL_USER_OWNED_BUCKET`.'
      ),
  )


def AddGcsSourceStagingDirFlag(parser, hidden=False):
  """Add a GCS directory flag for staging the build."""
  parser.add_argument(
      '--gcs-source-staging-dir',
      hidden=hidden,
      help=(
          'A directory in Google Cloud Storage to copy the source used for'
          ' staging the build. If the specified bucket does not exist, Cloud'
          " Build will create one. If you don't set this field,"
          ' ```gs://[PROJECT_ID]_cloudbuild/source``` is used or'
          ' ```gs://[PROJECT_ID]_[builds/region]_cloudbuild/source``` is used'
          ' when you set `--default-buckets-behavior` to'
          ' `REGIONAL_USER_OWNED_BUCKET` and `builds/region` is not `global`.'
      ),
  )


def AddIgnoreFileFlag(parser, hidden=False):
  """Add a ignore file flag."""
  parser.add_argument(
      '--ignore-file',
      hidden=hidden,
      help='Override the `.gcloudignore` file and use the specified file '
      'instead.')


def AddMachineTypeFlag(parser, hidden=False):
  """Add a machine type flag."""
  global _machine_type_flag_map
  _machine_type_flag_map = arg_utils.ChoiceEnumMapper(
      '--machine-type', (cloudbuild_util.GetMessagesModule()
                        ).BuildOptions.MachineTypeValueValuesEnum,
      include_filter=lambda s: six.text_type(s) != 'UNSPECIFIED',
      help_str='Machine type used to run the build.',
      hidden=hidden)
  _machine_type_flag_map.choice_arg.AddToParser(parser)


def AddSubstitutionsFlag(parser, hidden=False):
  """Add a substitutions flag."""
  parser.add_argument(
      '--substitutions',
      hidden=hidden,
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
Parameters to be substituted in the build specification.

For example (using some nonsensical substitution keys; all keys must begin with
an underscore):

    $ gcloud builds submit . --config config.yaml \\
        --substitutions _FAVORITE_COLOR=blue,_NUM_CANDIES=10

This will result in a build where every occurrence of ```${_FAVORITE_COLOR}```
in certain fields is replaced by "blue", and similarly for ```${_NUM_CANDIES}```
and "10".

Only the following built-in variables can be specified with the
`--substitutions` flag: REPO_NAME, BRANCH_NAME, TAG_NAME, REVISION_ID,
COMMIT_SHA, SHORT_SHA.

For more details, see:
https://cloud.google.com/cloud-build/docs/api/build-requests#substitutions
""")


def AddWorkerPoolFlag(parser, hidden=False):
  """Adds a flag to send the build to a workerpool.

  Args:
    parser: The argparse parser to add the arg to.
    hidden: If true, retain help but do not display it.

  Returns:
    worker pool flag group
  """
  worker_pools = parser.add_argument_group('Worker pool only flags.')
  worker_pools.add_argument(
      '--worker-pool',
      hidden=hidden,
      help='Specify a worker pool for the build to run in. Format: '
      'projects/{project}/locations/{region}/workerPools/{workerPool}.')

  return worker_pools


def AddTimeoutFlag(parser):
  """Add a timeout flag."""
  parser.add_argument(
      '--timeout',
      help='Maximum time a build is run before it is failed as `TIMEOUT`. It '
      'is specified as a duration; for example, "2h15m5s" is two hours, '
      'fifteen minutes, and five seconds. If you don\'t specify a unit, '
      'seconds is assumed. For example, "10" is 10 seconds.',
      action=actions.StoreProperty(properties.VALUES.builds.timeout))


def AddAsyncFlag(parser):
  """Add an async flag."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddSuppressLogsFlag(parser):
  """Add a flag to suppress logs."""
  parser.add_argument(
      '--suppress-logs',
      help='If set, build logs not streamed to stdout.',
      action='store_true')


def AddConfigFlags(parser):
  """Add config flags."""
  build_config = parser.add_mutually_exclusive_group()
  build_config.add_argument(
      '--tag',
      '-t',
      help='The tag to use with a "docker build" image creation. '
      'Cloud Build will run a remote "docker build -t '
      '$TAG .", where $TAG is the tag provided by this flag. The tag '
      'must be in the *gcr.io* or *pkg.dev* namespace. Specify a tag '
      'if you want Cloud Build to build using a Dockerfile '
      'instead of a build config file. If you specify a tag in this '
      'command, your source must include a Dockerfile. For instructions '
      'on building using a Dockerfile see '
      'https://cloud.google.com/cloud-build/docs/quickstart-build.')
  build_config.add_argument(
      '--config',
      default='cloudbuild.yaml',  # By default, find this in the current dir
      help='The YAML or JSON file to use as the build configuration file.')
  build_config.add_argument(
      '--pack',
      type=arg_parsers.ArgDict(spec={
          'image': str,
          'builder': str,
          'env': str
      }),
      action='append',
      help='Uses CNCF [buildpack](https://buildpacks.io/) to create image.  '
      'The "image" key/value must be provided.  The image name must be in the '
      '*gcr.io* or *pkg.dev* namespace. By default '
      '```gcr.io/buildpacks/builder``` will be used. To specify your own builder '
      'image use the optional "builder" key/value argument.  To pass '
      'environment variables to the builder use the optional "env" key/value '
      'argument where value is a list of key values using '
      '[escaping](https://cloud.google.com/sdk/gcloud/reference/topic/escaping) '
      'if necessary.'
  )


def AddConfigFlagsAlpha(worker_pools):
  """Add config flags."""
  worker_pools.add_argument(
      '--memory',
      type=arg_parsers.BinarySize(default_unit='GB'),
      hidden=True,
      help='Machine memory required to run a build.')
  worker_pools.add_argument(
      '--vcpu-count',
      type=float,
      hidden=True,
      help='Machine vCPU count required to run a build.')


def GetMachineType(machine_type_flag):
  """Return a machine type."""
  return _machine_type_flag_map.GetEnumForChoice(machine_type_flag)


def AddDefaultBucketsBehaviorFlag(parser):
  """Adds a default buckets behavior flag.

  Args:
    parser: The argparse parser to add the arg to.
  """
  GetDefaultBucketsBehaviorFlagMapper().choice_arg.AddToParser(parser)


def GetDefaultBucketsBehaviorFlagMapper(hidden=False):
  """Gets a mapper for default buckets behavior flag enum value.

  Args:
    hidden: If true, retain help but do not display it.

  Returns:
    A mapper for default buckets behavior flag enum value.
  """
  return arg_utils.ChoiceEnumMapper(
      '--default-buckets-behavior',
      (
          cloudbuild_util.GetMessagesModule()
      ).BuildOptions.DefaultLogsBucketBehaviorValueValuesEnum,
      include_filter=lambda s: six.text_type(s) != 'UNSPECIFIED',
      help_str='How default buckets are setup.',
      hidden=hidden,
  )


def GetDefaultBuckestBehavior(buckets_behavior_flag):
  """Returns default buckets behavior option.

  Args:
    buckets_behavior_flag: The string value of default buckets behavior flag.

  Returns:
    The enum of default buckets behavior flag.
  """
  return GetDefaultBucketsBehaviorFlagMapper().GetEnumForChoice(
      buckets_behavior_flag
  )
