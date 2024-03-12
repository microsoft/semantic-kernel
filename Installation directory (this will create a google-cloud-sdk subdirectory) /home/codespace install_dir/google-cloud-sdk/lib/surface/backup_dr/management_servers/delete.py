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
"""Deletes a Backup and DR Management Server."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.backupdr.management_servers import ManagementServersClient
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class DeleteAlpha(base.DeleteCommand):
  """Delete the specified Management Server."""

  detailed_help = {
      'BRIEF': 'Deletes a specific management server',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
        To delete a management server `sample-ms` in project `sample-project` and location `us-central1` , run:

          $ {command} sample-ms --project=sample-project --location=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddManagementServerResourceArg(
        parser,
        'Name of the management server to delete. Before you delete, take a'
        ' look at the prerequisites'
        ' [here](https://cloud.google.com/backup-disaster-recovery/docs/configuration/decommission).',
    )

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = ManagementServersClient()
    is_async = args.async_

    management_server = args.CONCEPTS.management_server.Parse()

    console_io.PromptContinue(
        message=(
            'The management server will be deleted. You cannot undo this'
            ' action.'
        ),
        default=True,
        cancel_on_no=True,
    )

    try:
      operation = client.Delete(management_server)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)
    if is_async:
      log.DeletedResource(
          operation.name,
          kind='management server',
          is_async=True,
          details=(
              'Run the [gcloud backup-dr operations describe] command '
              'to check the status of this operation.'
          ),
      )
      return operation

    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Deleting management server [{}]. (This operation could'
            ' take upto 1 hour.)'.format(management_server.RelativeName())
        ),
        has_result=False,
    )
