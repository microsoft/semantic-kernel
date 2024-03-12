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
"""'vmware external-addresses describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.externaladdresses import ExternalAddressesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe an external IP address in a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To get a description of an address called `first-ip` in the
          `my-privatecloud` private cloud in the `us-east2-b`
          location, run:

            $ {command} first-ip --private-cloud=my-privatecloud --location=us-east2-b --project=my-project

          Or:

            $ {command} first-ip --private-cloud=my-privatecloud

          In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an external IP address in a VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddExternalAddressArgToParser(parser)

  def Run(self, args):
    resource = args.CONCEPTS.external_address.Parse()
    client = ExternalAddressesClient()
    return client.Get(resource)
