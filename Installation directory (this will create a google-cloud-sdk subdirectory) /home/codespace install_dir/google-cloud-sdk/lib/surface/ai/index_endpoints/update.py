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
"""Vertex AI index endpoints update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.index_endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateV1(base.UpdateCommand):
  """Update an Vertex AI index endpoint.

  ## EXAMPLES

  To update display name of index endpoint `123` under project `example` in
  region `us-central1`, run:

    $ {command} --display-name=new-name --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddIndexEndpointResourceArg(parser, 'to update')
    flags.GetDisplayNameArg(
        'index endpoint', required=False).AddToParser(parser)
    flags.GetDescriptionArg('index endpoint').AddToParser(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def _Run(self, args, version):
    validation.ValidateDisplayName(args.display_name)
    index_endpoint_ref = args.CONCEPTS.index_endpoint.Parse()
    region = index_endpoint_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      index_endpoint_client = client.IndexEndpointsClient(version=version)
      try:
        if version == constants.GA_VERSION:
          result = index_endpoint_client.Patch(index_endpoint_ref, args)
        else:
          result = index_endpoint_client.PatchBeta(index_endpoint_ref, args)
      except errors.NoFieldsSpecifiedError:
        available_update_args = [
            'display_name', 'description', 'update_labels', 'clear_labels',
            'remove_labels'
        ]
        if not any(args.IsSpecified(arg) for arg in available_update_args):
          raise
        log.status.Print('No update to perform.')
        return None
      else:
        log.UpdatedResource(result.name, kind='Vertex AI index endpoint')
        return result

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateV1Beta1(UpdateV1):
  """Update an Vertex AI index endpoint.

  ## EXAMPLES

  To update display name of index endpoint `123` under project `example` in
  region `us-central1`, run:

    $ {command} --display-name=new-name --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
