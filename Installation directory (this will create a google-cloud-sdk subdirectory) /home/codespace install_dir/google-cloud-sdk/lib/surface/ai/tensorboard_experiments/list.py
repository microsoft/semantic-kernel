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
"""Command to list Tensorboard experiments in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboard_experiments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.core import resources


def _GetUriBeta(tensorboard):
  ref = resources.REGISTRY.ParseRelativeName(
      tensorboard.name,
      constants.TENSORBOARD_EXPERIMENTS_COLLECTION,
      api_version=constants.AI_PLATFORM_API_VERSION[constants.BETA_VERSION])
  return ref.SelfLink()


def _Run(args, version):
  tensorboard_ref = args.CONCEPTS.tensorboard.Parse()
  region = tensorboard_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(
      version=version, region=region):
    return client.TensorboardExperimentsClient(version=version).List(
        tensorboard_ref=tensorboard_ref,
        limit=args.limit,
        page_size=args.page_size,
        sort_by=args.sort_by)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(base.ListCommand):
  """List the Tensorboard experiments of the given project, region, and Tensorboard."""

  detailed_help = {
      'EXAMPLES':
          """\
          To list Tensorboard Experiments in Tensorboard `12345`:

              $ {command} 12345
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddTensorboardResourceArg(parser,
                                    'to create a Tensorboard experiment')
    parser.display_info.AddUriFunc(_GetUriBeta)

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
