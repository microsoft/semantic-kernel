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
"""'vmware private-connections delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateconnections import PrivateConnectionsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a Private Connection. When a private connection is deleted for a VMware Engine network, the connected network becomes inaccessible to that VMware Engine network.
        """,
    'EXAMPLES':
        """
          To delete a Private Connection resource called `my-private-connection` in project `my-project` and region `us-west1`, run:

            $ {command} my-private-connection --location=us-west1 --project=my-project

          Or:

            $ {command} my-private-connection

          In the second example, the project and the location is taken from gcloud properties core/project and compute/region, respectively.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Delete a Google Cloud Private Connection."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivateConnectionToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    private_connection = args.CONCEPTS.private_connection.Parse()
    client = PrivateConnectionsClient()
    is_async = args.async_
    operation = client.Delete(private_connection)
    if is_async:
      log.DeletedResource(
          operation.name, kind='Private Connection', is_async=True)
      return operation

    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for private connection [{}] to be deleted'.format(
            private_connection.RelativeName()),
        has_result=False)
