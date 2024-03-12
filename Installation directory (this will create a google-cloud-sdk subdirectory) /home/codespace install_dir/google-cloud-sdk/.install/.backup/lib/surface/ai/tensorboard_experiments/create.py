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
"""Vertex AI Tensorboard experiment create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboard_experiments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddArgs(parser):
  flags.AddTensorboardResourceArg(parser, 'to create a Tensorboard experiment')
  flags.GetDisplayNameArg(
      'tensorboard-experiment', required=False).AddToParser(parser)
  flags.GetDescriptionArg('tensorboard-experiment').AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)
  # Required=True
  flags.GetTensorboardExperimentIdArg().AddToParser(parser)


def _Run(args, version):
  """Create a new Vertex AI Tensorboard experiment."""
  validation.ValidateDisplayName(args.display_name)

  tensorboard_ref = args.CONCEPTS.tensorboard.Parse()
  region = tensorboard_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    tensorboard_experiments_client = client.TensorboardExperimentsClient(
        version=version)
    response = tensorboard_experiments_client.Create(tensorboard_ref, args)
    if response.name:
      log.status.Print(('Created Vertex AI Tensorboard experiment: {}.').format(
          response.name))
    return response


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(base.CreateCommand):
  """Create a new Vertex AI Tensorboard experiment."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Tensorboard Experiment in a Tensorboard `12345`, with the display name `my tensorboard experiment`:

              $ {command} 12345 --tensorboard-experiment-id=my-tensorboard-experiment --display-name="my tensorboard experiment"

          You may also provide a description and/or labels:

              $ {command} 12345 --tensorboard-experiment-id=my-tensorboard-experiment --description="my description" --labels="label1=value1" --labels="label2=value2"

          To create a Tensorboard Experiment `my-tensorboard-experiment` in a Tensorboard `12345`, region `us-central1`, and project `my-project`:

              $ {command} projects/my-project/locations/us-central1/tensorboards/12345 --tensorboard-experiment-id=my-tensorboard-experiment
          """,
  }

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
