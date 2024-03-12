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
"""'vmware network-policies list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networkpolicies import NetworkPoliciesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_policies import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VMware Engine network policies.
        """,
    'EXAMPLES':
        """
          To list network policies in your project in the region `us-west2` sorted from oldest to newest, run:

            $ {command} --location=us-west2 --project=my-project --sort-by=~create_time

          Or:

            $ {command}  --sort-by=~create_time

          In the second example, the project and the location are taken from gcloud properties core/project and compute/region respectively.

          To list network policies in your project from all regions, run:

            $ {command} --location=- --project=my-project

          Or:

            $ {command} --location=-

          In the last example, the project is taken from gcloud properties core/project.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List VMware Engine network policies."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=PROJECT,'
                                  'name.segment(-3):label=LOCATION,'
                                  'createTime,internetAccess,externalIp,'
                                  'edgeServicesCidr,vmwareEngineNetwork)')

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()
    client = NetworkPoliciesClient()
    return client.List(location)
