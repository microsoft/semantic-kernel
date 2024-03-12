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
"""Vertex AI indexes create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.indexes import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import indexes_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateV1(base.CreateCommand):
  """Create a new Vertex AI index.

  ## EXAMPLES

  To create an index under project `example` in region
  `us-central1`, encrypted with KMS key `kms-key-name`, run:

    $ {command} --display-name=index --description=test
    --metadata-file=path/to/your/metadata.json
    --project=example --region=us-central1
    --encryption-kms-key-name=kms-key-name
  """

  @staticmethod
  def Args(parser):
    flags.AddRegionResourceArg(
        parser,
        'to create index',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_OP_REGIONS
        ),
    )
    flags.GetDisplayNameArg('index').AddToParser(parser)
    flags.GetDescriptionArg('index').AddToParser(parser)
    flags.GetMetadataFilePathArg('index', required=True).AddToParser(parser)
    flags.GetMetadataSchemaUriArg('index').AddToParser(parser)
    flags.GetIndexUpdateMethod().AddToParser(parser)
    flags.GetEncryptionKmsKeyNameArg().AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def _Run(self, args, version):
    validation.ValidateDisplayName(args.display_name)
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    project_id = region_ref.AsDict()['projectsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      index_client = client.IndexesClient(version=version)
      if version == constants.GA_VERSION:
        operation = index_client.Create(region_ref, args)
      else:
        operation = index_client.CreateBeta(region_ref, args)

      op_ref = indexes_util.ParseIndexOperation(operation.name)
      index_id = op_ref.AsDict()['indexesId']
      log.status.Print(
          constants.OPERATION_CREATION_DISPLAY_MESSAGE.format(
              name=operation.name,
              verb='create index',
              id=op_ref.Name(),
              sub_commands='--index={} --region={} [--project={}]'.format(
                  index_id, region, project_id)))
      return operation

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateV1Beta1(CreateV1):
  """Create a new Vertex AI index.

  ## EXAMPLES

  To create an index under project `example` in region
  `us-central1`, encrypted with KMS key `kms-key-name`, run:

    $ {command} --display-name=index --description=test
    --metadata-file=path/to/your/metadata.json
    --project=example --region=us-central1
    --encryption-kms-key-name=kms-key-name
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
