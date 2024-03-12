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
"""Command to delete a Tensorboard time series in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.tensorboard_time_series import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import tensorboards_util


def _Run(args, version):
  tensorboard_time_series_ref = args.CONCEPTS.tensorboard_time_series.Parse()
  region = tensorboard_time_series_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(
      version=version, region=region):
    operation = client.TensorboardTimeSeriesClient(
        version=version).Delete(tensorboard_time_series_ref)
    return operations_util.WaitForOpMaybe(
        operations_client=operations.OperationsClient(),
        op=operation,
        op_ref=tensorboards_util.ParseTensorboardOperation(operation.name))


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an existing Vertex AI Tensorboard time series."""

  detailed_help = {
      'EXAMPLES':
          """\
          To delete a Tensorboard Time Series `123` in Tensorboard `12345`, Tensorboard Experiment `my-tensorboard-experiment`, Tensorboard Run `my-tensorboard-run`, region `us-central1`, and project `my-project`:

              $ {command} projects/my-project/locations/us-central1/tensorboards/12345/experiments/my-tensorboard-experiment/runs/my-tensorboard-run/timeSeries/123

          Or with flags:

              $ {command} 123 --tensorboard-id=12345 --tensorboard-experiment-id=my-tensorboard-experiment --tensorboard-run-id=my-tensorboard-run
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddTensorboardTimeSeriesResourceArg(parser, 'to delete')

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
