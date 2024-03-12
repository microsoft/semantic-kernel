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
"""ai-platform versions create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import operations
from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import region_util
from googlecloudsdk.command_lib.ml_engine import versions_util
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To create an AI Platform version model with the version ID 'versionId'
        and with the name 'model-name', run:

          $ {command} versionId --model=model-name
        """,
}


def _AddCreateArgs(parser):
  """Add common arguments for `versions create` command."""
  flags.GetModelName(positional=False, required=True).AddToParser(parser)
  flags.GetDescriptionFlag('version').AddToParser(parser)
  flags.GetRegionArg(include_global=True).AddToParser(parser)
  flags.VERSION_NAME.AddToParser(parser)
  base.Argument(
      '--origin',
      help="""\
          Location of ```model/``` "directory" (see
          https://cloud.google.com/ai-platform/prediction/docs/deploying-models#upload-model).

          This overrides `deploymentUri` in the `--config` file. If this flag is
          not passed, `deploymentUri` *must* be specified in the file from
          `--config`.

          Can be a Cloud Storage (`gs://`) path or local file path (no
          prefix). In the latter case the files will be uploaded to Cloud
          Storage and a `--staging-bucket` argument is required.
      """).AddToParser(parser)
  flags.RUNTIME_VERSION.AddToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  flags.STAGING_BUCKET.AddToParser(parser)
  base.Argument(
      '--config',
      help="""\
          Path to a YAML configuration file containing configuration parameters
          for the
          [Version](https://cloud.google.com/ai-platform/prediction/docs/reference/rest/v1/projects.models.versions)
          to create.

          The file is in YAML format. Note that not all attributes of a version
          are configurable; available attributes (with example values) are:

              description: A free-form description of the version.
              deploymentUri: gs://path/to/source
              runtimeVersion: '2.1'
              #  Set only one of either manualScaling or autoScaling.
              manualScaling:
                nodes: 10  # The number of nodes to allocate for this model.
              autoScaling:
                minNodes: 0  # The minimum number of nodes to allocate for this model.
              labels:
                user-defined-key: user-defined-value

          The name of the version must always be specified via the required
          VERSION argument.

          Only one of manualScaling or autoScaling can be specified. If both
          are specified in same yaml file an error will be returned.

          If an option is specified both in the configuration file and via
          command-line arguments, the command-line arguments override the
          configuration file.
      """
  ).AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)
  flags.FRAMEWORK_MAPPER.choice_arg.AddToParser(parser)
  flags.AddPythonVersionFlag(parser, 'when creating the version')
  flags.AddMachineTypeFlagToParser(parser)
  flags.GetAcceleratorFlag().AddToParser(parser)
  flags.AddAutoScalingFlags(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a new AI Platform version.

  Creates a new version of an AI Platform model.

  For more details on managing AI Platform models and versions see
  https://cloud.google.com/ai-platform/prediction/docs/managing-models-jobs
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _AddCreateArgs(parser)

  def Run(self, args):
    region = region_util.GetRegion(args)
    with endpoint_util.MlEndpointOverrides(region=region):
      client = versions_api.VersionsClient()
      labels = versions_util.ParseCreateLabels(client, args)
      framework = flags.FRAMEWORK_MAPPER.GetEnumForChoice(args.framework)
      accelerator = flags.ParseAcceleratorFlag(args.accelerator)
      return versions_util.Create(
          client,
          operations.OperationsClient(),
          args.version,
          model=args.model,
          origin=args.origin,
          staging_bucket=args.staging_bucket,
          runtime_version=args.runtime_version,
          config_file=args.config,
          asyncronous=args.async_,
          description=args.description,
          labels=labels,
          machine_type=args.machine_type,
          framework=framework,
          python_version=args.python_version,
          accelerator_config=accelerator,
          min_nodes=args.min_nodes,
          max_nodes=args.max_nodes,
          metrics=args.metric_targets,
          autoscaling_hidden=False)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create a new AI Platform version.

  Creates a new version of an AI Platform model.

  For more details on managing AI Platform models and versions see
  https://cloud.google.com/ai-platform/prediction/docs/managing-models-jobs
  """

  @staticmethod
  def Args(parser):
    _AddCreateArgs(parser)
    flags.SERVICE_ACCOUNT.AddToParser(parser)
    flags.AddUserCodeArgs(parser)
    flags.AddExplainabilityFlags(parser)
    flags.AddContainerFlags(parser)

  def Run(self, args):
    region = region_util.GetRegion(args)
    with endpoint_util.MlEndpointOverrides(region=region):
      client = versions_api.VersionsClient()
      labels = versions_util.ParseCreateLabels(client, args)
      framework = flags.FRAMEWORK_MAPPER.GetEnumForChoice(args.framework)
      accelerator = flags.ParseAcceleratorFlag(args.accelerator)
      return versions_util.Create(
          client,
          operations.OperationsClient(),
          args.version,
          model=args.model,
          origin=args.origin,
          staging_bucket=args.staging_bucket,
          runtime_version=args.runtime_version,
          config_file=args.config,
          asyncronous=args.async_,
          description=args.description,
          labels=labels,
          machine_type=args.machine_type,
          framework=framework,
          python_version=args.python_version,
          service_account=args.service_account,
          prediction_class=args.prediction_class,
          package_uris=args.package_uris,
          accelerator_config=accelerator,
          explanation_method=args.explanation_method,
          num_integral_steps=args.num_integral_steps,
          num_paths=args.num_paths,
          image=args.image,
          command=args.command,
          container_args=args.args,
          env_vars=args.env_vars,
          ports=args.ports,
          predict_route=args.predict_route,
          health_route=args.health_route,
          min_nodes=args.min_nodes,
          max_nodes=args.max_nodes,
          metrics=args.metric_targets,
          containers_hidden=False,
          autoscaling_hidden=False)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a new AI Platform version.

  Creates a new version of an AI Platform model.

  For more details on managing AI Platform models and versions see
  https://cloud.google.com/ai-platform/prediction/docs/managing-models-jobs
  """

  @staticmethod
  def Args(parser):
    CreateBeta.Args(parser)

  def Run(self, args):
    region = region_util.GetRegion(args)
    with endpoint_util.MlEndpointOverrides(region=region):
      client = versions_api.VersionsClient()
      labels = versions_util.ParseCreateLabels(client, args)
      framework = flags.FRAMEWORK_MAPPER.GetEnumForChoice(args.framework)
      accelerator = flags.ParseAcceleratorFlag(args.accelerator)
      return versions_util.Create(
          client,
          operations.OperationsClient(),
          args.version,
          model=args.model,
          origin=args.origin,
          staging_bucket=args.staging_bucket,
          runtime_version=args.runtime_version,
          config_file=args.config,
          asyncronous=args.async_,
          labels=labels,
          description=args.description,
          machine_type=args.machine_type,
          framework=framework,
          python_version=args.python_version,
          prediction_class=args.prediction_class,
          package_uris=args.package_uris,
          service_account=args.service_account,
          accelerator_config=accelerator,
          explanation_method=args.explanation_method,
          num_integral_steps=args.num_integral_steps,
          num_paths=args.num_paths,
          image=args.image,
          command=args.command,
          container_args=args.args,
          env_vars=args.env_vars,
          ports=args.ports,
          predict_route=args.predict_route,
          health_route=args.health_route,
          min_nodes=args.min_nodes,
          max_nodes=args.max_nodes,
          metrics=args.metric_targets,
          containers_hidden=False,
          autoscaling_hidden=False)
