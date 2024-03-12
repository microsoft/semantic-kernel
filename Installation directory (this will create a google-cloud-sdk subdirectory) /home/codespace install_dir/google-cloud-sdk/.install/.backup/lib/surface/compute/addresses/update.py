# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to update labels for addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine address.

  *{command}* updates labels for a Compute Engine
  address.

  ## EXAMPLES

  To add/update labels 'k0' and 'k1' and remove labels with key 'k3' for address
  'example-address', run:

    $ {command} example-address --region=us-central1 \
      --update-labels=k0=value1,k1=value2 --remove-labels=k3

  Labels can be used to identify the address and to filter them as in:

    $ {parent_command} list --filter='labels.k1:value2'

  To list existing labels for address 'example-address', run:

    $ {parent_command} describe example-address --format="default(labels)"

  """

  ADDRESS_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ADDRESS_ARG = flags.AddressArgument(plural=False)
    cls.ADDRESS_ARG.AddArgument(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    address_ref = self.ADDRESS_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if not labels_diff.MayHaveUpdates():
      raise calliope_exceptions.RequiredArgumentException(
          'LABELS', 'At least one of --update-labels or '
          '--remove-labels must be specified.')

    if address_ref.Collection() == 'compute.globalAddresses':
      address = client.globalAddresses.Get(
          messages.ComputeGlobalAddressesGetRequest(**address_ref.AsDict()))
      labels_value = messages.GlobalSetLabelsRequest.LabelsValue
    else:
      address = client.addresses.Get(
          messages.ComputeAddressesGetRequest(**address_ref.AsDict()))
      labels_value = messages.RegionSetLabelsRequest.LabelsValue

    labels_update = labels_diff.Apply(labels_value, address.labels)

    if not labels_update.needs_update:
      return address

    if address_ref.Collection() == 'compute.globalAddresses':
      request = messages.ComputeGlobalAddressesSetLabelsRequest(
          project=address_ref.project,
          resource=address_ref.Name(),
          globalSetLabelsRequest=messages.GlobalSetLabelsRequest(
              labelFingerprint=address.labelFingerprint,
              labels=labels_update.labels))

      operation = client.globalAddresses.SetLabels(request)
      operation_ref = holder.resources.Parse(
          operation.selfLink, collection='compute.globalOperations')

      operation_poller = poller.Poller(client.globalAddresses)
    else:
      request = messages.ComputeAddressesSetLabelsRequest(
          project=address_ref.project,
          resource=address_ref.Name(),
          region=address_ref.region,
          regionSetLabelsRequest=messages.RegionSetLabelsRequest(
              labelFingerprint=address.labelFingerprint,
              labels=labels_update.labels))

      operation = client.addresses.SetLabels(request)
      operation_ref = holder.resources.Parse(
          operation.selfLink, collection='compute.regionOperations')

      operation_poller = poller.Poller(client.addresses)

    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating labels of address [{0}]'.format(address_ref.Name()))
