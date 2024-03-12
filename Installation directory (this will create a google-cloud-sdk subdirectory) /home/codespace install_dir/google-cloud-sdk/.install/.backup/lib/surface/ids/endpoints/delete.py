# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'ids endpoints delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.calliope import base
from googlecloudsdk.api_lib.ids import ids_api
from googlecloudsdk.command_lib.ids import flags
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a Cloud IDS endpoint.
        """,
    'EXAMPLES':
        """
          To delete an endpoint called `my-ep` in project `my-project`
          and zone `us-central1-a`, run:

          $ {command} my-ep --project=my-project --zone=us-central1-a

          OR

          $ {command} projects/myproject/locations/us-central1-a/endpoints/my-ep

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Cloud IDS endpoint."""

  @staticmethod
  def Args(parser):
    flags.AddEndpointResource(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.

  def Run(self, args):
    endpoint = args.CONCEPTS.endpoint.Parse()
    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    client = ids_api.Client(self.ReleaseTrack())
    operation = client.DeleteEndpoint(endpoint.RelativeName())

    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for endpoint [{}] to be deleted'.format(
            endpoint.RelativeName()),
        has_result=False,
        max_wait=max_wait)


Delete.detailed_help = DETAILED_HELP
