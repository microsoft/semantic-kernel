# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""'vmware nodes describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.nodes import NodesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION': """
        Display data associated with a VMware Engine node, such as its name, state, node type, ip, fqdn.
      """,
    'EXAMPLES': """
        To describe a node called `my-node` in private cloud `my-private-cloud` cluster `my-cluster` and zone `us-west2-a`, run:

          $ {command} my-node --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --cluster=my-cluster

          Or:

          $ {command} my-node --private-cloud=my-private-cloud --cluster=my-cluster

         In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
  """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Google Cloud VMware Engine node."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNodeArgToParser(parser)

  def Run(self, args):
    node = args.CONCEPTS.node.Parse()
    client = NodesClient()
    return client.Get(node)
