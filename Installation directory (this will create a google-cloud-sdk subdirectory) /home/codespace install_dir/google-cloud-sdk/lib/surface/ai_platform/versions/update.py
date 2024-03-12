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
"""ai-platform versions update command."""

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
from googlecloudsdk.core import log


def _AddUpdateArgs(parser):
  """Get arguments for the `ai-platform versions update` command."""
  flags.AddVersionResourceArg(parser, 'to update')
  flags.GetDescriptionFlag('version').AddToParser(parser)
  flags.GetRegionArg(include_global=True).AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)
  base.Argument(
      '--config',
      metavar='YAML_FILE',
      help="""\
          Path to a YAML configuration file containing configuration parameters
          for the
          [version](https://cloud.google.com/ml/reference/rest/v1/projects.models.versions)
          to create.

          The file is in YAML format. Note that not all attributes of a version
          are configurable; available attributes (with example values) are:

              description: A free-form description of the version.
              manualScaling:
                nodes: 10  # The number of nodes to allocate for this model.
              autoScaling:
                minNodes: 0  # The minimum number of nodes to allocate for this model.
                maxNodes: 1  # The maxinum number of nodes to allocate for this model.
              requestLoggingconfig:
                bigqueryTableName: someTable  # Fully qualified BigQuery table name.
                samplingPercentage: 0.5  # Percentage of requests to be logged.

          The name of the version must always be specified via the required
          VERSION argument.

          Only one of manualScaling or autoScaling can be specified. If both
          are specified in same yaml file, an error will be returned.

          Labels cannot currently be set in the config.yaml; please use
          the command-line flags to alter them.

          If an option is specified both in the configuration file and via
          command-line arguments, the command-line arguments override the
          configuration file.
      """
  ).AddToParser(parser)


def _Run(args):
  region = region_util.GetRegion(args)
  with endpoint_util.MlEndpointOverrides(region=region):
    versions_client = versions_api.VersionsClient()
    operations_client = operations.OperationsClient()
    version_ref = args.CONCEPTS.version.Parse()
    versions_util.Update(versions_client, operations_client, version_ref, args)
    log.UpdatedResource(args.version, kind='AI Platform version')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an AI Platform version."""

  @staticmethod
  def Args(parser):
    _AddUpdateArgs(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update an AI Platform version."""

  @staticmethod
  def Args(parser):
    _AddUpdateArgs(parser)
    flags.AddRequestLoggingConfigFlags(parser)

  def Run(self, args):
    return _Run(args)
