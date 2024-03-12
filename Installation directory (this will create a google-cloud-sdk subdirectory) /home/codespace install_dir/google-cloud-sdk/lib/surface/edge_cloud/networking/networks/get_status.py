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
"""Command to get the status of a Distributed Cloud Edge Network network."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.networks import networks
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args

DESCRIPTION = (
    'Get the status of a specified Distributed Cloud Edge Network network.')
EXAMPLES = """\
    To get the status of the Distributed Cloud Edge Network network
    'my-network' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-network --location=us-central1 --zone=us-central1-edge-den1

   """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetStatus(base.Command):
  """Get the status of a specified Distributed Cloud Edge Network network.

  *{command}* is used to get the status of a Distributed Cloud Edge Network
  network.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddNetworkResourceArg(parser, 'to get status', True)

  def Run(self, args):
    networks_client = networks.NetworksClient(self.ReleaseTrack())
    network_ref = args.CONCEPTS.network.Parse()
    return networks_client.GetStatus(network_ref)
