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
"""Command to cancel an operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import operations as op_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.core import log

_EXAMPLES = """
To cancel an operation in location ``us-west1'', run:

$ {command} OPERATION_ID --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Cancel(base.Command):
  """Cancel an operation."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddOperationResourceArg(parser, 'to cancel')

  def Run(self, args):
    """Runs the cancel command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseOperationResourceArg(args).locationsId,
        self.ReleaseTrack(),
    ):
      op_client = op_api_util.OperationsClient()
      op_ref = resource_args.ParseOperationResourceArg(args)
      op = op_client.Get(op_ref)
      command_util.CancelOperationPrompt(op.name)
      op_client.Cancel(op_ref)
      log.status.Print(command_util.CancelOperationMessage(op.name, 'aws'))
      return op_client.Get(op_ref)
