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
"""'vmware networks describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networks import NetworksClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.networks import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a VMware Engine network.
        """,
    'EXAMPLES':
        """
          To get a description of a network called `my-network` of type `STANDARD` in project `my-project` and region `global`, run:

            $ {command} my-network --location=global --project=my-project

          Or:

            $ {command} my-network

          In the second example, the project is taken from gcloud properties core/project and the location is taken as `global`.

          To get a description of a network called `my-network` of type `LEGACY` in project `my-project` and region `us-west2`, run:

            $ {command} my-network --location=us-west2 --project=my-project

          Or:

            $ {command} my-network --location=us-west2

          In the last example, the project is taken from gcloud properties core/project. For VMware Engine networks of type `LEGACY`, you must always specify a region as the location.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Google Cloud VMware Engine network."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkToParser(parser, positional=True)

  def Run(self, args):
    network = args.CONCEPTS.vmware_engine_network.Parse()
    client = NetworksClient()
    return client.Get(network)
