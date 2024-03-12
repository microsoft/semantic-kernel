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
"""Flags for the deploy command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

_SOURCE_HELP_TEXT = """
The location of the source that contains skaffold.yaml. The location can be a directory on a local disk or a gzipped archive file (.tar.gz) in Google Cloud Storage.
 If the source is a local directory, this command skips the files specified in the --ignore-file. If --ignore-file is not specified, use.gcloudignore file. If a .gcloudignore file is absent and a .gitignore file is present in the local source directory, gcloud will use a generated Git-compatible .gcloudignore file that respects your .gitignored files.
 The global .gitignore is not respected. For more information on .gcloudignore, see gcloud topic gcloudignore.
"""


def AddGcsSourceStagingDirFlag(parser, hidden=False):
  """Adds a Google Cloud Storage directory flag for staging the build."""
  parser.add_argument(
      '--gcs-source-staging-dir',
      hidden=hidden,
      help=(
          'A directory in Google Cloud Storage to copy the source used for '
          'staging the build. If the specified bucket does not exist, Cloud '
          "Deploy will create one. If you don't set this field, "
          '```gs://[DELIVERY_PIPELINE_ID]_clouddeploy/source``` is used.'
      ),
  )


def AddIgnoreFileFlag(parser, hidden=False):
  """Adds an ignore file flag."""
  parser.add_argument(
      '--ignore-file',
      hidden=hidden,
      help=(
          'Override the `.gcloudignore` file and use the specified file '
          'instead.'
      ),
  )


def AddToTargetFlag(parser, hidden=False):
  """Adds to-target flag."""
  parser.add_argument(
      '--to-target',
      hidden=hidden,
      help='Specifies a target to deliver into upon release creation',
  )


def AddImagesGroup(parser, hidden=False):
  """Adds Images flag."""
  images_group = parser.add_mutually_exclusive_group()
  images_group.add_argument(
      '--images',
      metavar='NAME=TAG',
      type=arg_parsers.ArgDict(),
      hidden=hidden,
      help=textwrap.dedent("""\
      Reference to a collection of individual image name to image full path replacements.

      For example:

          $ gcloud deploy releases create foo \\
              --images image1=path/to/image1:v1@sha256:45db24
      """),
  )
  images_group.add_argument(
      '--build-artifacts',
      hidden=hidden,
      help=(
          'Reference to a Skaffold build artifacts output file from skaffold'
          " build --file-output=BUILD_ARTIFACTS. If you aren't using Skaffold,"
          ' use the --images flag below to specify the'
          ' image-names-to-tagged-image references.'
      ),
  )


def AddConfigFile(parser, hidden=False):
  """Adds config flag."""
  parser.add_argument(
      '--file',
      hidden=hidden,
      required=True,
      help=(
          'Path to yaml file containing Delivery Pipeline(s), Target(s)'
          ' declarative definitions.'
      ),
  )


def AddToTarget(parser, hidden=False):
  """Adds to-target flag."""
  parser.add_argument(
      '--to-target', hidden=hidden, help='Destination target to promote into.'
  )


def AddRolloutID(parser, hidden=False):
  """Adds rollout-id flag."""
  parser.add_argument(
      '--rollout-id',
      hidden=hidden,
      help='ID to assign to the generated rollout for promotion.',
  )


def AddRelease(parser, help_text, hidden=False):
  """Adds release flag."""
  parser.add_argument('--release', hidden=hidden, help=help_text)


def AddForce(parser, help_text, hidden=False):
  """Adds force flag."""
  parser.add_argument(
      '--force',
      hidden=hidden,
      action='store_true',
      help=help_text,
  )


def AddDescription(parser, help_text, name='--description'):
  """Adds description related flag."""
  parser.add_argument(
      name,
      help=help_text,
  )


def AddDeliveryPipeline(parser, required=True):
  """Adds delivery pipeline flag."""
  parser.add_argument(
      '--delivery-pipeline',
      help='The name of the Cloud Deploy delivery pipeline',
      required=required,
  )


def AddAnnotationsFlag(parser, resource_type):
  """Adds --annotations flag."""
  help_text = textwrap.dedent("""\
  Annotations to apply to the %s. Annotations take the form of key/value string pairs.

  Examples:

  Add annotations:

    $ {command} --annotations="from_target=test,status=stable"

  """) % (resource_type)

  parser.add_argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text,
  )


def AddLabelsFlag(parser, resource_type):
  """Add --labels flag."""
  help_text = textwrap.dedent("""\
  Labels to apply to the %s. Labels take the form of key/value string pairs.

  Examples:

  Add labels:

    $ {command} --labels="commit=abc123,author=foo"

""") % (resource_type)

  parser.add_argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text,
  )


def AddSkaffoldVersion(parser):
  """Adds skaffold version flag."""
  parser.add_argument(
      '--skaffold-version', help='Version of the Skaffold binary.'
  )


def AddSkaffoldFileFlag():
  """Add --skaffold-file flag."""
  help_text = textwrap.dedent("""\
  Path of the skaffold file absolute or relative to the source directory.

  Examples:

  Use Skaffold file with relative path:
  The current working directory is expected to be some part of the skaffold path (e.g. the current working directory could be /home/user)

    $ {command} --source=/home/user/source --skaffold-file=config/skaffold.yaml

  The skaffold file absolute file path is expected to be:
  /home/user/source/config/skaffold.yaml


  Use Skaffold file with absolute path and with or without source argument:


    $ {command} --source=/home/user/source --skaffold-file=/home/user/source/config/skaffold.yaml

    $ {command} --skaffold-file=/home/user/source/config/skaffold.yaml

  """)
  return base.Argument('--skaffold-file', help=help_text)


def AddSourceFlag():
  """Adds source flag."""
  return base.Argument(
      '--source', help=_SOURCE_HELP_TEXT, default='.'
  )  # By default, the current directory is used.


def AddKubernetesFileFlag():
  return base.Argument(
      '--from-k8s-manifest',
      help=(
          'The path to a Kubernetes manifest, which Cloud Deploy will use to '
          'generate a skaffold.yaml file for you (for example, '
          'foo/bar/k8.yaml). The generated Skaffold file will be available in '
          'the Google Cloud Storage source staging directory (see '
          '--gcs-source-staging-dir flag) after the release is complete.'
      ),
  )


def AddCloudRunFileFlag():
  return base.Argument(
      '--from-run-manifest',
      help=(
          'The path to a Cloud Run manifest, which Cloud Deploy will use to'
          ' generate a skaffold.yaml file for you (for example,'
          ' foo/bar/service.yaml). The generated Skaffold file will be'
          ' available in the Google Cloud Storage source staging directory (see'
          ' --gcs-source-staging-dir flag) after the release is complete.'
      ),
  )


def AddServicesFlag():
  return base.Argument(
      '--services',
      metavar='NAME=TAG',
      type=arg_parsers.ArgDict(),
      hidden=True,
      help="""
        The flag to be used with the --from-run-container flag to specify the
        name of the service present in a given target.
        This will be a repeated flag.

        *target_id*::: The target_id.
        *service*::: The name of the service in the specified target_id.

        For example:

          $gcloud deploy releases create foo \\
              --from-run-container=path/to/image1:v1@sha256:45db24
              --services=dev_target:dev_service
              --services=prod_target:prod_service
      """,
  )


def AddFromRunContainerFlag():
  return base.Argument(
      '--from-run-container',
      hidden=True,
      help="""
          The container name, which Cloud Deploy will use to
          generate a CloudRun manifest.yaml and a skaffold.yaml file.
          The generated Skaffold file and manifest file will be
          available in the Google Cloud Storage source staging directory
          after the release is complete.
      """,
  )


def AddSkaffoldSources(parser):
  """Add Skaffold sources."""
  skaffold_source_config_group = parser.add_mutually_exclusive_group()
  # Add a group that contains the skaffold-file and source flags to a mutex
  # group.
  skaffold_source_group = skaffold_source_config_group.add_group(mutex=False)
  AddSkaffoldFileFlag().AddToParser(skaffold_source_group)
  AddSourceFlag().AddToParser(skaffold_source_group)
  # Add the from-k8s-manifest and --from-run-manifest flag to the mutex group.
  AddKubernetesFileFlag().AddToParser(skaffold_source_config_group)
  AddCloudRunFileFlag().AddToParser(skaffold_source_config_group)
  # Add from-k8s-container and the from-run-container flag to the mutex group.
  run_container_group = skaffold_source_config_group.add_group(mutex=False,
                                                               hidden=True)
  AddFromRunContainerFlag().AddToParser(run_container_group)
  AddServicesFlag().AddToParser(run_container_group)


def AddDescriptionFlag(parser):
  """Add --description flag."""
  parser.add_argument(
      '--description',
      help='Description of rollout created during a rollback.',
      hidden=False,
      default=None,
      required=False,
  )


def AddListAllPipelines(parser):
  """Add --list-all-pipelines flag."""
  help_text = textwrap.dedent("""\
  List all Delivery Pipelines associated with a target.

  Usage:

    $ {command} --list-all-pipelines

""")

  parser.add_argument(
      '--list-all-pipelines', action='store_true', default=None, help=help_text
  )


def AddSkipPipelineLookup(parser):
  """Add --skip-pipeline-lookup flag."""
  help_text = textwrap.dedent("""\
  If set, skip fetching details of associated pipelines when describing a target.

  Usage:

    $ {command} --skip-pipeline-lookup

""")

  parser.add_argument(
      '--skip-pipeline-lookup',
      action='store_true',
      default=False,
      help=help_text,
  )


def AddRollbackOfRollout(parser):
  """Add --rollback-of-rollout flag."""
  help_text = textwrap.dedent("""\
  If set, this validates whether the rollout name specified by the flag matches
  the rollout on the target.

  Examples:

  Validate that `test-rollout` is the rollout to rollback on the target.

    $ {command} --rollback-of-rollout=projects/test-project/locations/us-central1/deliveryPipelines/test-pipeline/releases/test-release/rollouts/test-rollout

  """)

  parser.add_argument(
      '--rollback-of-rollout',
      help=help_text,
      hidden=False,
      # By default, None is used.
      default=None,
      required=False,
  )


def AddStartingPhaseId(parser):
  """Add --starting-phase-id flag."""
  help_text = textwrap.dedent("""\
  If set, starts the created rollout at the specified phase.

  Start rollout at `stable` phase:

    $ {command} --starting-phase-id=stable

  """)

  parser.add_argument(
      '--starting-phase-id',
      help=help_text,
      hidden=False,
      # By default, None is used.
      default=None,
      required=False,
  )


def AddInitialRolloutLabelsFlag():
  """Add --initial-rollout-labels flag."""
  help_text = textwrap.dedent("""\
  Labels to apply to the initial rollout when creating the release. Labels take
  the form of key/value string pairs.

  Examples:

  Add labels:

    $ {command} initial-rollout-labels="commit=abc123,author=foo"

""")
  return base.Argument(
      '--initial-rollout-labels',
      help=help_text,
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
  )


def AddInitialRolloutAnnotationsFlag():
  """Adds --initial-rollout-annotations flag."""
  help_text = textwrap.dedent("""\
  Annotations to apply to the initial rollout when creating the release.
  Annotations take the form of key/value string pairs.

  Examples:

  Add annotations:

    $ {command} --initial-rollout-annotations="from_target=test,status=stable"

  """)

  return base.Argument(
      '--initial-rollout-annotations',
      help=help_text,
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
  )


def AddInitialRolloutPhaseIDFlag():
  """Adds --initial-rollout-phase-id flag."""
  help_text = textwrap.dedent("""\
  The phase to start the initial rollout at when creating the release.
  The phase ID must be a valid phase on the rollout. If not specified, then the
  rollout will start at the first phase.

  Examples:

  Start rollout at `stable` phase:

    $ {command} --initial-rollout-phase-id=stable

  """)

  return base.Argument(
      '--initial-rollout-phase-id',
      help=help_text,
      hidden=False,
      # By default, None is used.
      default=None,
      required=False,
  )


def AddEnableInitialRolloutFlag():
  """Adds --enable-initial-rollout flag."""

  return base.Argument(
      '--enable-initial-rollout',
      action='store_const',
      help=(
          'Creates a rollout in the first target defined in the delivery'
          ' pipeline. This is the default behavior.'
      ),
      const=True,
  )


def AddDisableInitialRolloutFlag():
  """Adds --disable-initial-rollout flag."""

  return base.Argument(
      '--disable-initial-rollout',
      action='store_const',
      help=(
          'Skips creating a rollout in the first target defined in the delivery'
          ' pipeline.'
      ),
      const=True,
  )


def AddInitialRolloutGroup(parser):
  """Adds initial-rollout flag group."""
  group = parser.add_mutually_exclusive_group()
  # Create a group that contains the flags to enable an initial rollout and add
  # labels and annotations to that rollout. The group itself is mutually
  # exclusive of the disable initial rollout group.
  enable_initial_rollout_group = group.add_group(mutex=False)
  AddInitialRolloutLabelsFlag().AddToParser(enable_initial_rollout_group)
  AddInitialRolloutAnnotationsFlag().AddToParser(enable_initial_rollout_group)
  AddInitialRolloutPhaseIDFlag().AddToParser(enable_initial_rollout_group)
  AddEnableInitialRolloutFlag().AddToParser(enable_initial_rollout_group)
  # Add the disable initial rollout flag to the mutex group.
  AddDisableInitialRolloutFlag().AddToParser(group)


def AddJobId(parser, hidden=False):
  """Adds job-id flag."""
  parser.add_argument(
      '--job-id',
      hidden=hidden,
      help='Job ID on a rollout resource',
      required=True,
  )


def AddPhaseId(parser, required=True, hidden=False):
  """Adds phase-id flag."""
  parser.add_argument(
      '--phase-id',
      hidden=hidden,
      help='Phase ID on a rollout resource',
      required=required,
  )


def AddDeployParametersFlag(parser, hidden=False):
  """Add --deploy-parameters flag."""
  help_text = textwrap.dedent("""\
  Deployment parameters to apply to the release. Deployment parameters take the form of key/value string pairs.

  Examples:

  Add deployment parameters:

    $ {command} --deploy-parameters="key1=value1,key2=value2"

""")

  parser.add_argument(
      '--deploy-parameters',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      hidden=hidden,
      help=help_text,
  )


def AddOverrideDeployPolicies(parser, hidden=True):
  """Adds override-deploy-policies flag."""
  parser.add_argument(
      '--override-deploy-policies',
      metavar='POLICY',
      hidden=hidden,
      type=arg_parsers.ArgList(),
      help='Deploy policies to override',
  )
