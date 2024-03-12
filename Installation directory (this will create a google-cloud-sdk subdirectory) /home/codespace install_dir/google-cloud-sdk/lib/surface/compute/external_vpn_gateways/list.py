# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to list the External VPN Gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.external_vpn_gateways import flags
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List Compute Engine external VPN gateways."""

  detailed_help = {
      'EXAMPLES':
          """\
          To list all external VPN gateways, run:

              $ {command}"""
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)

  def Run(self, args):
    """Issues the request to list all external VPN gateways."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    project = properties.VALUES.core.project.Get(required=True)

    request = messages.ComputeExternalVpnGatewaysListRequest(
        project=project, filter=args.filter)

    return list_pager.YieldFromList(
        client.externalVpnGateways,
        request,
        field='items',
        limit=args.limit,
        batch_size=None)


List.detailed_help = base_classes.GetGlobalListerHelp('external VPN gateways')
