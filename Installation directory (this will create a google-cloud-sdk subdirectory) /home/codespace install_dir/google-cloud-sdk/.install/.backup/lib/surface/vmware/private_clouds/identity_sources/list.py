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
"""'vmware private-clouds identity-sources list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.identitysources import IdentitySourcesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

_DETAILED_HELP = {
    'DESCRIPTION': """
        List identity source resources in a given private cloud.
    """,
    'EXAMPLES': """
        To retrieve all identity sources from a private cloud `my-pc` located  in project `my-project` and zone `us-west1-a`:

          $ {command} --project=my-project --location=us-west1-a --private-cloud=my-pc

          Or:

          $ {command} --private-cloud=my-pc

        In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone` respectively.
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine identity sources in a given private cloud."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,'
        'name.segment(-5):label=LOCATION,'
        'name.segment(-3):label=PRIVATE_CLOUD,'
        'vmware_identity_source,appliance_type,domain,domain_user)'
    )

  def Run(self, args):
    pc = args.CONCEPTS.private_cloud.Parse()
    client = IdentitySourcesClient()
    return client.List(pc)
