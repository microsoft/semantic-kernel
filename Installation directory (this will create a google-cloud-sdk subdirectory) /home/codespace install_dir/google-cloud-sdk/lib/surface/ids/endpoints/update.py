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
"""Update endpoint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.ids import ids_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ids import flags
from googlecloudsdk.core import exceptions as core_exceptions

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update the endpoint for the specified VPC network. Check the
          progress of endpoint update by using `gcloud alpha ids endpoints
          list`.

          For more examples, refer to the EXAMPLES section below.


        """,
    'EXAMPLES':
        """
            To update an endpoint called `my-endpoint`, excluding threat IDs
            1000 and 2000, run:

            $ {command} my-endpoint --threat-exceptions=1000,2000

            To update an endpoint called `my-endpoint`, clearing the excluded
            threat list, run:

            $ {command} my-endpoint --threat-exceptions=

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class UpdateAlpha(base.UpdateCommand):
  """Update an existing Cloud IDS endpoint."""

  @staticmethod
  def Args(parser):
    flags.AddEndpointResource(parser)
    flags.AddThreatExceptionsArg(parser, required=False)
    flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    client = ids_api.Client(self.ReleaseTrack())

    endpoint = args.CONCEPTS.endpoint.Parse()
    update_mask = []

    if args.IsSpecified('threat_exceptions'):
      threat_exceptions = args.threat_exceptions
      update_mask.append('threat_exceptions')
    else:
      raise core_exceptions.Error('Missing --threat-exceptions.')
    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.UpdateEndpoint(
        endpoint.RelativeName(),
        threat_exceptions=threat_exceptions,
        update_mask=update_mask)
    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for endpoint [{}] to be updated'.format(
            endpoint.RelativeName()),
        max_wait=max_wait)


UpdateAlpha.detailed_help = DETAILED_HELP
