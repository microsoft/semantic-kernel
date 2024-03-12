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
"""'vmware private-clouds management-dns-zone-bindings list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.managementdnszonebinding import ManagementDNSZoneBindingClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION': """
          List management DNS zone bindings in a VMware Engine private cloud.
        """,
    'EXAMPLES': """
          To list management DNS zone bindings in the `my-private-cloud` private cloud, run:

            $ {command} --private-cloud=my-private-cloud --project=my-project --location=us-east2-b
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List management DNS zone bindings in a VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=PROJECT,'
                                  'name.segment(-3):label=PRIVATE_CLOUD,'
                                  'firstof(vmwareEngineNetwork,vpcNetwork):'
                                  'label=BIND_NETWORK,'
                                  'createTime,state)')

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = ManagementDNSZoneBindingClient()
    return client.List(privatecloud, limit=args.limit)
