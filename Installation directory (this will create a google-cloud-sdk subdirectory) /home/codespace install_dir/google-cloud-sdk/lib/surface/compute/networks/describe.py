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
"""Command for describing networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import networks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.core.resource import resource_projector


class Describe(base.DescribeCommand):
  r"""Describe a Compute Engine network.

  *{command}* displays all data associated with Compute Engine
  network in a project.

  ## EXAMPLES

  To describe a network with the name 'network-name', run:

    $ {command} network-name

  """

  NETWORK_ARG = None

  @staticmethod
  def Args(parser):
    Describe.NETWORK_ARG = flags.NetworkArgument()
    Describe.NETWORK_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    network_ref = self.NETWORK_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeNetworksGetRequest(**network_ref.AsDict())
    response = client.MakeRequests(
        [(client.apitools_client.networks, 'Get', request)])

    resource_dict = resource_projector.MakeSerializable(response[0])
    return networks_utils.AddModesForListFormat(resource_dict)
