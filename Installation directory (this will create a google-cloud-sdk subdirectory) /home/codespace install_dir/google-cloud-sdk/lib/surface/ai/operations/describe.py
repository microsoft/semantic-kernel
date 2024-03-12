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
"""Vertex AI operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import index_endpoints_util
from googlecloudsdk.command_lib.ai import indexes_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeV1(base.DescribeCommand):
  """Gets detailed index information about the given operation id.

  ## EXAMPLES

  To describe an operation `123` of project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1

  To describe an operation `123` belongs to parent index resource `456` of
  project `example` in region `us-central1`, run:

    $ {command} 123 --index=456 --project=example --region=us-central1

  To describe an operation `123` belongs to parent index endpoint resource `456`
  of project `example` in region `us-central1`, run:

    $ {command} 123 --index-endpoint=456 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddOperationResourceArg(parser)
    flags.GetIndexIdArg(
        required=False,
        helper_text="""\
     ID of the index. Applies to operations belongs to an index resource. Do not set otherwise.
    """).AddToParser(parser)
    flags.GetIndexEndpointIdArg(
        required=False,
        helper_text="""\
     ID of the index endpoint. Applies to operations belongs to an index endpoint resource. Do not set otherwise.
    """).AddToParser(parser)

  def _Run(self, args, version):
    # This is the default operation name in the format of
    # `projects/123/locations/us-central1/operations/456`.
    operation_ref = args.CONCEPTS.operation.Parse()
    project_id = operation_ref.AsDict()['projectsId']
    region = operation_ref.AsDict()['locationsId']
    operation_id = operation_ref.AsDict()['operationsId']

    if args.index is not None:
      # Override the operation name using the multi-parent format.
      operation_ref = indexes_util.BuildIndexParentOperation(
          project_id, region, args.index, operation_id)
    elif args.index_endpoint is not None:
      operation_ref = index_endpoints_util.BuildParentOperation(
          project_id, region, args.index_endpoint, operation_id)
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      return operations.OperationsClient(version=version).Get(operation_ref)

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DescribeV1Beta1(DescribeV1):
  """Gets detailed index information about the given operation id.

  ## EXAMPLES

  To describe an operation `123` of project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1

  To describe an operation `123` belongs to parent index resource `456` of
  project `example` in region `us-central1`, run:

    $ {command} 123 --index=456 --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
