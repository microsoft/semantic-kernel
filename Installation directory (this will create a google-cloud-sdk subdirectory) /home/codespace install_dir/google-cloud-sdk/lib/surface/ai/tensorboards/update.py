# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Vertex AI endpoints update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboards import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddArgs(parser):
  flags.AddTensorboardResourceArg(parser, 'to update')
  flags.GetDisplayNameArg('tensorboard', required=False).AddToParser(parser)
  flags.GetDescriptionArg('tensorboard').AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)


def _Run(args, version):
  """Update an existing Vertex AI Tensorboard."""

  tensorboard_ref = args.CONCEPTS.tensorboard.Parse()
  args.region = tensorboard_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    tensorboards_client = client.TensorboardsClient(version=version)

    try:
      op = tensorboards_client.Patch(tensorboard_ref, args)
    except errors.NoFieldsSpecifiedError:
      available_update_args = [
          'display_name',
          'description',
          'update_labels',
          'clear_labels',
          'remove_labels',
      ]
      if not any(args.IsSpecified(arg) for arg in available_update_args):
        raise
      log.status.Print('No update to perform.')
      return None
    else:
      log.UpdatedResource(op.name, kind='Vertex AI Tensorboard')
      return op


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGa(base.UpdateCommand):
  """Update an existing Vertex AI Tensorboard."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Tensorboard `12345`, in region `us-central1` and project `my-project`, with the display name `updated display name`:

              $ {command} projects/my-project/locations/us-central1/tensorboards/12345 --display-name="updated display name"
          """,
  }

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateBeta(base.UpdateCommand):
  """Update an existing Vertex AI Tensorboard."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Tensorboard `12345`, in region `us-central1` and project `my-project`, with the display name `updated display name`:

              $ {command} projects/my-project/locations/us-central1/tensorboards/12345 --display-name="updated display name"
          """,
  }

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
