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
"""'Marketplace Solutions ssh keys describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.mps.mps_client import MpsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.mps import flags
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a Marketplace Solutions ssh_key.
        """,
    'EXAMPLES':
        """
          To get a description of an ssh-key called `my-ssh-key' in
          project `my-project'' and region ``us-central1', run:

          $ {command} my-ssh-key --project=my-project --region=us-central1
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Marketplace Solutions ssh-key."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSSHKeyArgToParser(parser, positional=True)

  def Run(self, args):
    """Return ssh key description information based on user request."""
    ssh_key = args.CONCEPTS.ssh_key.Parse()
    product = properties.VALUES.mps.product.Get(required=True)
    client = MpsClient()
    return client.GetSSHKey(product, ssh_key)


Describe.detailed_help = DETAILED_HELP

