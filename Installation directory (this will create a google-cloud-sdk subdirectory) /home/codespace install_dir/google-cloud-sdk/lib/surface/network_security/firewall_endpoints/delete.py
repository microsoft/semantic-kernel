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
"""Delete endpoint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import activation_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Delete a firewall endpoint. Check the progress of endpoint deletion
          by using `gcloud network-security firewall-endpoints list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To delete a firewall endpoint called `my-endpoint`, in zone
            `us-central1-a` and organization ID 1234, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234

            OR

            $ {command} organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    activation_flags.AddEndpointResource(cls.ReleaseTrack(), parser)
    activation_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    client = activation_api.Client(self.ReleaseTrack())

    endpoint = args.CONCEPTS.firewall_endpoint.Parse()

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.DeleteEndpoint(
        name=endpoint.RelativeName(),
    )
    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for firewall endpoint [{}] to be deleted'.format(
            endpoint.RelativeName()
        ),
        has_result=False,
        max_wait=max_wait,
    )


Delete.detailed_help = DETAILED_HELP
