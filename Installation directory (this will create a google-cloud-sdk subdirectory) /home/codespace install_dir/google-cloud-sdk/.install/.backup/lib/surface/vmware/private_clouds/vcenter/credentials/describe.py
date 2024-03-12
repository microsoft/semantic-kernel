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
"""'vmware vcenter credentials describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Retrieve VMware vCenter sign-in credentials associated with a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To get sign-in credentials for vCenter in private cloud `my-private-cloud`, run:


            $ {command} --private-cloud=my-private-cloud --location=us-west2-a --project=my-project

          Or:

            $ {command} --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone`.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe Google Cloud VMware Engine vCenter credentials."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    parser.add_argument(
        '--username',
        hidden=True,
        help="""\
        The username of the user to be queried for credentials.
        """,
    )

  def Run(self, args):
    resource = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    return client.GetVcenterCredentials(resource, args.username)
