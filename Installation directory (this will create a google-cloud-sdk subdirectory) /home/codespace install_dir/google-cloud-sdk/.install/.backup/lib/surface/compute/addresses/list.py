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
"""Command for listing addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.addresses import flags
import six


def _TransformAddressRange(resource):
  prefix_length = resource.get('prefixLength')
  address = resource.get('address')
  if prefix_length:
    return address + '/' + six.text_type(prefix_length)
  return address


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List addresses."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          address_range():label=ADDRESS/RANGE,
          address_type:label=TYPE,
          purpose,
          network.basename(),
          region.basename(),
          subnetwork.basename():label=SUBNET,
          status
        )""")
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)
    parser.display_info.AddCacheUpdater(flags.AddressesCompleter)
    parser.display_info.AddTransforms({'address_range': _TransformAddressRange})

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        regional_service=client.apitools_client.addresses,
        global_service=client.apitools_client.globalAddresses,
        aggregation_service=client.apitools_client.addresses)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = {
    'brief':
        'List addresses',
    'DESCRIPTION':
        """
        *{command}* lists summary information of addresses in a project. The
        *--uri* option can be used to display URIs instead. Users who want to
        see more data should use `gcloud compute addresses describe`.

        By default, global addresses and addresses from all regions are listed.
        The results can be narrowed down by providing the *--regions* or
        *--global* flag.
        """,
    'EXAMPLES':
        """
        To list all addresses in a project in table form, run:

          $ {command}

        To list the URIs of all addresses in a project, run:

          $ {command} --uri

        To list all of the global addresses in a project, run:

          $ {command} --global

        To list all of the addresses from the ``us-central1'' region, run:

          $ {command} --filter=region:us-central1
        """,
}
