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
"""'vmware network-policies describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networkpolicies import NetworkPoliciesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_policies import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a VMware Engine network policy.
        """,
    'EXAMPLES':
        """
          To get a description of a network policy called `my-network-policy` in project `my-project` and region `us-west2`, run:

            $ {command} my-network-policy --location=us-west2 --project=my-project

          Or:

            $ {command} my-network-policy

          In the second example, the project and the location are taken from gcloud properties core/project and compute/region respectively.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a VMware Engine network policy."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkPolicyToParser(parser, positional=True)

  def Run(self, args):
    network_policy = args.CONCEPTS.network_policy.Parse()
    client = NetworkPoliciesClient()
    return client.Get(network_policy)
