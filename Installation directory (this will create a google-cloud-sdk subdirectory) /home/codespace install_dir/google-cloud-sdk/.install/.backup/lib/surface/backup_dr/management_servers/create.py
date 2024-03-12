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
"""Creates a new Backup and DR Management Server."""


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


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create a new management server in the project."""

  detailed_help = {
      'BRIEF': 'Creates a new management server',
      'DESCRIPTION': (
          '{description} A management server is required to access the'
          ' management console. It can only be created in locations where'
          ' Backup and DR is available. Resources in other locations can be'
          ' backed up.'
      ),
      'EXAMPLES': """\
        To create a new management server `sample-ms` in project `sample-project` and location `us-central1` with network `sample-network`, run:

          $ {command} sample-ms --project=sample-project --location=us-central1 --network=projects/sample-project/global/networks/sample-network
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
        'Name of the management server to be created. Once the management'
        " server is deployed, this name can't be changed. The name must be"
        ' unique for a project and location.',
    )
    flags.AddNetwork(parser)

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
    network = args.network

    try:
      operation = client.Create(management_server, network)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)
    if is_async:
      log.CreatedResource(
          operation.name,
          kind='management server',
          is_async=True,
          details=(
              'Run the [gcloud backup-dr operations describe] command '
              'to check the status of this operation.'
          ),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Creating management server [{}]. (This operation could'
            ' take upto 1 hour.)'.format(management_server.RelativeName())
        ),
    )
    log.CreatedResource(
        management_server.RelativeName(), kind='management server'
    )

    return resource
