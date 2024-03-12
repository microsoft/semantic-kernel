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
"""Command for deleting addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.addresses import flags


class Delete(base.DeleteCommand):
  r"""Release reserved IP addresses.

  *{command}* releases one or more Compute Engine IP addresses.

  ## EXAMPLES

  To release an address with the name 'address-name', run:

    $ {command} address-name

  To release two addresses with the names 'address-name1' and 'address-name2',
  run:

    $ {command} address-name1 address-name2
  """

  ADDRESSES_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ADDRESSES_ARG = flags.AddressArgument(required=True)
    cls.ADDRESSES_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.AddressesCompleter)

  def Run(self, args):
    """Issues requests necessary to delete Addresses."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    address_refs = self.ADDRESSES_ARG.ResolveAsResource(
        args, holder.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(address_refs)
    requests = []
    for address_ref in address_refs:
      if address_ref.Collection() == 'compute.globalAddresses':
        request = client.messages.ComputeGlobalAddressesDeleteRequest(
            address=address_ref.Name(),
            project=address_ref.project,
        )
        requests.append((client.apitools_client.globalAddresses, 'Delete',
                         request))
      elif address_ref.Collection() == 'compute.addresses':
        request = client.messages.ComputeAddressesDeleteRequest(
            address=address_ref.Name(),
            project=address_ref.project,
            region=address_ref.region,
        )
        requests.append((client.apitools_client.addresses, 'Delete', request))

    return client.MakeRequests(requests)
