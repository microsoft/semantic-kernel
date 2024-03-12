# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Abort operation command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

CANCEL_OPERATION_MESSAGE = (
    'Cancelation of operation {0} has been requested. '
    'Please use gcloud container operations describe {1} to '
    'check if the operation has been canceled successfully.')


class Cancel(base.Command):
  """Cancel an operation."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('operation_id', help='The operation id to cancel.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)
    op_ref = adapter.ParseOperation(args.operation_id, location)
    try:
      op = adapter.GetOperation(op_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    console_io.PromptContinue(
        message='Are you sure you want to cancel operation {0}?'.format(
            op.name),
        throw_if_unattended=True,
        cancel_on_no=True)

    try:
      adapter.CancelOperation(op_ref)
      log.status.Print(
          CANCEL_OPERATION_MESSAGE.format(args.operation_id, args.operation_id))
      return adapter.GetOperation(op_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


Cancel.detailed_help = {
    'brief':
        'Cancel a running operation.',
    'DESCRIPTION':
        """
        Cancel a running operation.

Cancel is a best-effort method for aborting a running operation. Operations that
have already completed can not be cancelled. If the operation has passed the
"point of no-return", cancel will have no effect.

An example of "point of no-return" in the context of Upgrade operations would
be if all the nodes have been upgraded but the operation hasn't been marked as
complete.
""",
    'EXAMPLES':
        """\
        To cancel an operation, run:

          $ {command} sample-operation-id
        """,
}
