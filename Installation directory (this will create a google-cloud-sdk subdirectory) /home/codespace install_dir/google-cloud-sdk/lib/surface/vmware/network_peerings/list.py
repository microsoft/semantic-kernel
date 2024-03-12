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
"""VMware engine vpc network list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import networkpeering
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_peerings import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VPC network peerings across all locations in your project.

        """,
    'EXAMPLES':
        """
          To list all the VPC network peerings created on or after April 12, 2021, sorted from oldest to newest, run:

            $ {command} --filter="createTime > 2021-04-12T00:00:00.00Z" --sort-by=createTime

          In this example, the location is taken as `global`.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine VPC network peerings."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=PROJECT,'
                                  'name.segment(-3):label=LOCATION,'
                                  'createTime,state)')

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()
    client = networkpeering.NetworkPeeringClient()
    return client.List(location)
