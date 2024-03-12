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
"""Update endpoint association command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.network_security.firewall_endpoint_associations import association_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.network_security import association_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions

DETAILED_HELP = {
    'DESCRIPTION': """
          Update a firewall endpoint association. Check the progress of
          association update by using
            `gcloud network-security firewall-endpoint-associations describe`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
          To update labels k1 and k2, run:

            $ {command} my-assoc --zone=us-central1-a --project=my-proj --update-labels=k1=v1,k2=v2

          To remove labels k3 and k4, run:

            $ {command} my-assoc --zone=us-central1-a --project=my-proj --remove-labels=k3,k4

          To clear all labels from the firewall endpoint association, run:

            $ {command} my-assoc --zone=us-central1-a --project=my-proj --clear-labels
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update a Firewall Plus endpoint association."""

  _valid_arguments = [
      '--clear-labels',
      '--remove-labels',
      '--update-labels',
      '--[no-]tls-inspection-policy',
      '--[no-]disabled',
  ]

  @classmethod
  def Args(cls, parser):
    association_flags.AddAssociationResource(cls.ReleaseTrack(), parser)
    association_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

    outer_group = parser.add_mutually_exclusive_group()

    association_flags.AddDisabledArg(outer_group)

    tls_and_labels_group = outer_group.add_group()
    labels_util.AddUpdateLabelsFlags(tls_and_labels_group)

    tls_group = tls_and_labels_group.add_mutually_exclusive_group()
    association_flags.AddTLSInspectionPolicy(cls.ReleaseTrack(), tls_group)
    association_flags.AddNoTLSInspectionPolicyArg(tls_group)

  def Run(self, args):
    """Updates an association with labels and TLS inspection policy.

    Args:
      args: argparse.Namespace, the parsed arguments.

    Returns:
      A long running operation if async is set, None otherwise.
    """
    client = association_api.Client(self.ReleaseTrack())
    update_fields = {}
    association = args.CONCEPTS.firewall_endpoint_association.Parse()
    original = client.DescribeAssociation(association.RelativeName())
    if original is None:
      raise exceptions.InvalidArgumentException(
          'firewall-endpoint-association',
          'Firewall endpoint association does not exist.',
      )

    if args.IsSpecified('disabled'):
      update_fields['disabled'] = getattr(args, 'disabled', False)

    if args.IsSpecified('tls_inspection_policy'):
      parsed_policy = args.CONCEPTS.tls_inspection_policy.Parse()
      if parsed_policy is None:
        raise core_exceptions.Error(
            'TLS Inspection Policy resource path is either empty, malformed,'
            ' or missing necessary flag'
            ' `--tls-inspection-policy-region`.\nNOTE: TLS Inspection Policy'
            ' needs to be in the same region as Firewall Plus endpoint'
            ' resource.'
        )
      update_fields['tls_inspection_policy'] = parsed_policy.RelativeName()
    elif getattr(args, 'no_tls_inspection_policy', False):
      # We use an empty value to remove the policy.
      update_fields['tls_inspection_policy'] = ''

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      update_fields['labels'] = original.labels
      labels_update = labels_diff.Apply(
          client.messages.FirewallEndpointAssociation.LabelsValue,
          original.labels,
      )
      if labels_update.needs_update:
        update_fields['labels'] = labels_update.labels

    if not update_fields:
      raise exceptions.MinimumArgumentException(self._valid_arguments)

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.UpdateAssociation(
        name=association.RelativeName(),
        update_fields=update_fields,
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
        message=(
            'waiting for firewall endpoint association [{}] to be updated'
            .format(association.RelativeName())
        ),
        has_result=True,
        max_wait=max_wait,
    )


Update.detailed_help = DETAILED_HELP
