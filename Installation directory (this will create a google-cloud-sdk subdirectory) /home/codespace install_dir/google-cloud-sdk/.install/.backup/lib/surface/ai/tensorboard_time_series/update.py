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
"""Command to update a Tensorboard time series in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboard_time_series import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.core import log


def _AddArgs(parser):
  flags.AddTensorboardTimeSeriesResourceArg(parser, 'to update')
  flags.GetDisplayNameArg(
      'tensorboard time series', required=False).AddToParser(parser)
  flags.GetDescriptionArg('tensorboard time series').AddToParser(parser)
  flags.GetPluginNameArg('tensorboard-time-series').AddToParser(parser)
  flags.GetPluginDataArg('tensorboard-time-series').AddToParser(parser)


def _Run(args, version):
  """Update an existing Vertex AI Tensorboard time series."""
  tensorboard_time_series_ref = args.CONCEPTS.tensorboard_time_series.Parse()
  args.region = tensorboard_time_series_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    try:
      op = client.TensorboardTimeSeriesClient(version=version).Patch(
          tensorboard_time_series_ref, args)
    except errors.NoFieldsSpecifiedError:
      available_update_args = [
          'display_name', 'description', 'plugin_name', 'plugin_data'
      ]
      if not any(args.IsSpecified(arg) for arg in available_update_args):
        raise
      log.status.Print('No update to perform.')
      return None
    else:
      log.UpdatedResource(op.name, kind='Vertex AI Tensorboard time series')
      return op


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateBeta(base.UpdateCommand):
  """Update an existing Vertex AI Tensorboard time series."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Tensorboard Time Series `123` in Tensorboard `12345`, Tensorboard Experiment `my-tensorboard-experiment`, Tensorboard Run `my-tensorboard-run`, region `us-central1`, and project `my-project`, with the display name `updated display name`:

              $ {command} projects/my-project/locations/us-central1/tensorboards/12345/experiments/my-tensorboard-experiment/runs/my-tensorboard-run/timeSeries/123 --display-name="updated display name"

          Or with flags:

              $ {command} 123 --tensorboard-id=12345 --tensorboard-experiment-id=my-tensorboard-experiment --tensorboard-run-id=my-tensorboard-run --display-name="updated display name"
          """,
  }

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
