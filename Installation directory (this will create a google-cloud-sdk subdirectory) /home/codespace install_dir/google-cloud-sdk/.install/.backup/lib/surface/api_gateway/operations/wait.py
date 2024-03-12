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

"""`gcloud api-gateway operations wait` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Wait(base.Command):
  """Wait for a Cloud API Gateway operation to complete."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To wait for a Cloud API Gateway operation named ``NAME'' in the ``us-central1''
          region, run:

            $ {command} NAME --location=us-central1

          To wait for a Cloud API Gateway operation with a resource name of ``RESOURCE'',
          run:

            $ {command} RESOURCE

          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArgs(parser, 'poll')

  def Run(self, args):
    client = operations.OperationsClient()
    operation_ref = args.CONCEPTS.operation.Parse()

    # To give a better message for already-completed operations, get the
    # operation here and check if it's already completed.
    operation = client.Get(operation_ref)

    if operation.done:
      msg_prefix = 'Operation has already completed.'
    else:
      # No need to check for the result, errors and timeouts are handled already
      client.WaitForOperation(operation_ref)

      msg_prefix = 'Operation completed successfully.'

    log.status.Print('{} Use the following command for more details:\n\n'
                     'gcloud api-gateway operations describe {}\n'.format(
                         msg_prefix,
                         operation_ref.RelativeName()))
