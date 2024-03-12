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
"""Vertex AI index endpoints delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.index_endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import index_endpoints_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeleteV1(base.DeleteCommand):
  """Delete an existing Vertex AI index endpoint.

  ## EXAMPLES

  To delete an index endpoint `123` of project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddIndexEndpointResourceArg(parser, 'to delete')

  def _Run(self, args, version):
    index_endpoint_ref = args.CONCEPTS.index_endpoint.Parse()
    region = index_endpoint_ref.AsDict()['locationsId']
    index_endpoint_id = index_endpoint_ref.AsDict()['indexEndpointsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      console_io.PromptContinue(
          'This will delete index endpoint [{}]...'.format(index_endpoint_id),
          cancel_on_no=True)
      operation = client.IndexEndpointsClient(
          version=version).Delete(index_endpoint_ref)
      return operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(version=version),
          op=operation,
          op_ref=index_endpoints_util.ParseIndexEndpointOperation(
              operation.name))

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteV1Beta1(DeleteV1):
  """Delete an existing Vertex AI index endpoint.

  ## EXAMPLES

  To delete an index endpoint `123` of project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
