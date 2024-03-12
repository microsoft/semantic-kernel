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
"""Create endpoint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'DESCRIPTION': """
          Create a firewall endpoint. Successful creation of an endpoint results
          in an endpoint in READY state. Check the progress of endpoint creation
          by using `gcloud network-security firewall-endpoints list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To create a firewall endpoint called `my-endpoint`, in zone
            `us-central1-a` and organization ID 1234, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    activation_flags.AddEndpointResource(cls.ReleaseTrack(), parser)
    activation_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    activation_flags.AddDescriptionArg(parser)
    activation_flags.AddBillingProjectArg(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args, target_firewall_attachment=None, endpoint_type=None):
    client = activation_api.Client(self.ReleaseTrack())

    endpoint = args.CONCEPTS.firewall_endpoint.Parse()
    labels = labels_util.ParseCreateArgs(
        args, client.messages.FirewallEndpoint.LabelsValue
    )

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.CreateEndpoint(
        name=endpoint.Name(),
        parent=endpoint.Parent().RelativeName(),
        description=getattr(args, 'description', None),
        billing_project_id=args.billing_project,
        labels=labels,
        target_firewall_attachment=target_firewall_attachment,
        endpoint_type=endpoint_type,
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
        message='waiting for firewall endpoint [{}] to be created'.format(
            endpoint.RelativeName()
        ),
        has_result=True,
        max_wait=max_wait,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    activation_flags.AddTargetFirewallAttachmentArg(parser)

  def Run(self, args):
    target_firewall_attachment = getattr(
        args, 'target_firewall_attachment', None
    )

    if target_firewall_attachment is not None:
      return self._Run(
          args, target_firewall_attachment, endpoint_type='THIRD_PARTY'
      )
    else:
      return self._Run(
          args, target_firewall_attachment, endpoint_type='TYPE_UNSPECIFIED'
      )


Create.detailed_help = DETAILED_HELP
