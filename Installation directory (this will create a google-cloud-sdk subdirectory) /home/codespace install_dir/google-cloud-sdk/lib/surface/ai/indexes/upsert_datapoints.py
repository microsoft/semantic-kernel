# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Vertex AI indexes upsert datapoints command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.indexes import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpsertDatapointsV1(base.CreateCommand):
  """Upsert data points into the specified index.

  ## EXAMPLES

  To upsert datapoints into an index '123', run:

    $ {command} 123 --datapoints-from-file=example.json
    --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddIndexResourceArg(parser, 'to upsert data points from')
    flags.GetDatapointsFilePathArg('index', required=True).AddToParser(parser)
    flags.GetDynamicMetadataUpdateMaskArg(required=False).AddToParser(parser)

  def _Run(self, args, version):
    index_ref = args.CONCEPTS.index.Parse()
    region = index_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      index_client = client.IndexesClient(version=version)
      if version == constants.GA_VERSION:
        operation = index_client.UpsertDatapoints(index_ref, args)
      else:
        operation = index_client.UpsertDatapointsBeta(index_ref, args)
      return operation

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpsertDatapointsV1Beta1(UpsertDatapointsV1):
  """Upsert data points into the specified index.

  ## EXAMPLES

  To upsert datapoints into an index `123`, run:

    $ {command} 123 --datapoints-from-file=example.json
    --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
