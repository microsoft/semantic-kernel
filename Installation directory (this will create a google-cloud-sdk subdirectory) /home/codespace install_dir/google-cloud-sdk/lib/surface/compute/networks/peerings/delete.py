# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for deleting network peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Delete(base.DeleteCommand):
  r"""Delete a Compute Engine network peering.

  *{command}* deletes a Compute Engine network peering.

  ## EXAMPLES

  To delete a network peering with the name 'peering-name' on the network
  'local-network', run:

    $ {command} peering-name \
      --network=local-network

  """

  @staticmethod
  def Args(parser):

    parser.add_argument('name', help='The name of the peering to delete.')

    parser.add_argument(
        '--network',
        required=True,
        help='The name of the network in the current project containing the '
        'peering.')

  def Run(self, args):
    """Issues the request necessary for deleting the peering."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request = client.messages.ComputeNetworksRemovePeeringRequest(
        network=args.network,
        networksRemovePeeringRequest=(
            client.messages.NetworksRemovePeeringRequest(name=args.name)),
        project=properties.VALUES.core.project.GetOrFail())

    return client.MakeRequests([(client.apitools_client.networks,
                                 'RemovePeering', request)])
