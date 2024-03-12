# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'vmware sddc clusters list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.sddc.ipaddresses import IPAddressesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.sddc import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List external ip addresses in a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To list external ip addresses in the ``my-privatecloud'' private cloud, run:

            $ {command} --privatecloud=my-privatecloud
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List external ip addresses in a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=PROJECT,'
                                  'name.segment(-3):label=PRIVATECLOUD,'
                                  'internalIp,externalIp,createTime,state)')

  def Run(self, args):
    privatecloud = args.CONCEPTS.privatecloud.Parse()
    client = IPAddressesClient()
    return client.List(privatecloud)


List.detailed_help = DETAILED_HELP
