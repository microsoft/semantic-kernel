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
"""Vertex AI indexes delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.indexes import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import indexes_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeleteV1(base.DeleteCommand):
  """Delete an existing Vertex AI index.

  ## EXAMPLES

  To delete an index `123` of project `example` in region `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddIndexResourceArg(parser, 'to delete')

  def _Run(self, args, version):
    index_ref = args.CONCEPTS.index.Parse()
    region = index_ref.AsDict()['locationsId']
    index_id = index_ref.AsDict()['indexesId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      console_io.PromptContinue(
          'This will delete index [{}]...'.format(index_id), cancel_on_no=True)
      operation = client.IndexesClient(version=version).Delete(index_ref)
      return operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(),
          op=operation,
          op_ref=indexes_util.ParseIndexOperation(operation.name))

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteV1Beta1(DeleteV1):
  """Delete an existing Vertex AI index.

  ## EXAMPLES

  To delete an index `123` of project `example` in region `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
