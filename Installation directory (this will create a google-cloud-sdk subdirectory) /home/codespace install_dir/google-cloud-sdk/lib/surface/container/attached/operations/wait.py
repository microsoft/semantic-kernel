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
"""Command to wait for an operation to complete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import operations as op_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util

_EXAMPLES = """
To wait for an operation in location ``us-west1'' to complete, run:

$ {command} OPERATION_ID --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Wait for an operation to complete."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddOperationResourceArg(parser, 'to wait for')

  def Run(self, args):
    """Runs the wait command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseOperationResourceArg(args).locationsId,
        self.ReleaseTrack(),
    ):
      op_client = op_api_util.OperationsClient()
      op_ref = resource_args.ParseOperationResourceArg(args)
      op_client.Wait(
          op_ref,
          'Waiting for operation {} to complete'.format(op_ref.RelativeName()),
      )
      return op_client.Get(op_ref)
