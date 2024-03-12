# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.metastore import operations_util as operations_api_util
from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.metastore import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {'EXAMPLES': """\
          To cancel an active Dataproc Metastore operation with the name
          `operation-1` in location `us-central1`, run:

          $ {command} operation-1 --location=us-central1
        """}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Cancel(base.Command):
  """Cancel a Dataproc Metastore operation."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'cancel')

  def Run(self, args):
    operation_ref = args.CONCEPTS.operation.Parse()

    console_io.PromptContinue(
        message='Cancel the following operation: [%s] in [%s].\n'
        % (operation_ref.operationsId, operation_ref.locationsId),
        cancel_on_no=True,
        cancel_string='Cancellation aborted by user.',
        throw_if_unattended=True,
    )

    try:
      operations_api_util.Cancel(
          operation_ref.RelativeName(), release_track=self.ReleaseTrack()
      )
      log.status.Print('Cancelled operation [{0}].'.format(args.operation))
    except apitools_exceptions.HttpError as e:
      exc = exceptions.HttpException(e)
      log.status.Print(
          'ERROR: Failed to cancel operation [{0}]: {1}.'.format(
              args.operation, exc.payload.status_message
          )
      )
      raise api_util.Error('Cancellation did not succeed.')
