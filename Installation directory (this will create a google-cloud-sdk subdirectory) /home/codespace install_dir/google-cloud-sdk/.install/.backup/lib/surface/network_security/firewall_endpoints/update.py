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
"""Update endpoint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'DESCRIPTION': """
          Update a firewall endpoint. Check the progress of endpoint update
          by using `gcloud network-security firewall-endpoints describe`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To update labels k1 and k2, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234 --update-labels=k1=v1,k2=v2

            To remove labels k3 and k4, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234 --remove-labels=k3,k4

            To clear all labels from the firewall endpoint, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234 --clear-labels
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update a Firewall Plus endpoint.

  This command is used to update labels on the endpoint.
  """

  @classmethod
  def Args(cls, parser):
    activation_flags.AddEndpointResource(cls.ReleaseTrack(), parser)
    activation_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    activation_flags.AddDescriptionArg(parser)
    activation_flags.AddUpdateBillingProjectArg(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = activation_api.Client(self.ReleaseTrack())

    endpoint = args.CONCEPTS.firewall_endpoint.Parse()
    original = client.DescribeEndpoint(endpoint.RelativeName())
    if original is None:
      raise exceptions.InvalidArgumentException(
          'firewall-endpoint',
          'Firewall endpoint does not exist.')

    update_mask = []

    labels = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      update_mask.append('labels')
      labels = original.labels
      labels_update = labels_diff.Apply(
          client.messages.FirewallEndpoint.LabelsValue,
          original.labels,
      )
      if labels_update.needs_update:
        labels = labels_update.labels

    billing_project_id = args.update_billing_project
    if billing_project_id:
      update_mask.append('billing_project_id')

    if not update_mask:
      raise exceptions.MinimumArgumentException([
          '--clear-labels',
          '--remove-labels',
          '--update-labels',
          '--update-billing-project',
      ])

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.UpdateEndpoint(
        name=endpoint.RelativeName(),
        description=getattr(args, 'description', None),
        update_mask=','.join(update_mask),
        labels=labels,
        billing_project_id=billing_project_id,
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
        message='waiting for firewall endpoint [{}] to be updated'.format(
            endpoint.RelativeName()
        ),
        has_result=True,
        max_wait=max_wait,
    )


Update.detailed_help = DETAILED_HELP
