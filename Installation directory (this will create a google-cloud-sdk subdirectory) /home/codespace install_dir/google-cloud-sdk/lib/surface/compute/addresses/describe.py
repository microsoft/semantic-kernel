# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags


class Describe(base.DescribeCommand):
  r"""Display detailed information about a reserved static address.

  *{command}* displays all data associated with a reserved static address in a
  project.

  ## EXAMPLES
  To get details about a global address, run:

    $ {command} my-address-name --global

  To get details about a regional address, run:

    $ {command} my-address-name --region=us-central1
  """

  ADDRESS_ARG = None

  @staticmethod
  def Args(parser):
    Describe.ADDRESS_ARG = flags.AddressArgument(plural=False)
    Describe.ADDRESS_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    """Issues request necessary to describe the Addresses."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    address_ref = Describe.ADDRESS_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if address_ref.Collection() == 'compute.addresses':
      service = client.apitools_client.addresses
      request = client.messages.ComputeAddressesGetRequest(
          **address_ref.AsDict())
    elif address_ref.Collection() == 'compute.globalAddresses':
      service = client.apitools_client.globalAddresses
      request = client.messages.ComputeGlobalAddressesGetRequest(
          **address_ref.AsDict())

    return client.MakeRequests([(service, 'Get', request)])[0]
