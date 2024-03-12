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
"""Vertex AI Tensorboard run create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ai.tensorboard_runs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddArgs(parser):
  flags.AddTensorboardExperimentResourceArg(parser,
                                            'to create a Tensorboard run')
  flags.GetDisplayNameArg('tensorboard-run', required=True).AddToParser(parser)
  flags.GetDescriptionArg('tensorboard-run').AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)
  flags.GetTensorboardRunIdArg(required=True).AddToParser(parser)


def _Run(args, version):
  """Create a new Vertex AI Tensorboard run."""
  tensorboard_exp_ref = args.CONCEPTS.tensorboard_experiment.Parse()
  region = tensorboard_exp_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    tensorboard_runs_client = client.TensorboardRunsClient(version=version)
    response = tensorboard_runs_client.Create(tensorboard_exp_ref, args)
    response_msg = encoding.MessageToPyValue(response)
    if 'name' in response_msg:
      log.status.Print(('Created Vertex AI Tensorboard run: {}.').format(
          response_msg['name']))
    return response


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(base.CreateCommand):
  """Create a new Vertex AI Tensorboard run."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Tensorboard Run `my-tensorboard-run` in Tensorboard `12345` and Tensorboard Experiment `my-tensorboard-experiment, with the display name `my tensorboard run`:

              $ {command} my-tensorboard-experiment --tensorboard-run-id=my-tensorboard-run --tensorboard-id=12345 --display-name="my tensorboard run"

          You may also provide a description and/or labels:

              $ {command} my-tensorboard-experiment --tensorboard-run-id=my-tensorboard-run --tensorboard-id=12345 --description="my description" --labels="label1=value1" --labels="label2=value2"

          To create a Tensorboard Run `my-tensorboard-run` in Tensorboard `12345`, Tensorboard Experiment `my-tensorboard-experiment, region `us-central1`, and project `my-project`:

              $ {command} projects/my-project/locations/us-central1/tensorboards/12345/experiments/my-tensorboard-experiment --tensorboard-run-id=my-tensorboard-run
          """,
  }

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    validation.ValidateDisplayName(args.display_name)
    return _Run(args, constants.BETA_VERSION)
