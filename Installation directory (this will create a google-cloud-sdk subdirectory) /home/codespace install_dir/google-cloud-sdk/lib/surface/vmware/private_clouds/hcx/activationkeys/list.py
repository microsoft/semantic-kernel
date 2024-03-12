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
"""'vmware hcx activationkeys list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.hcxactivationkeys import HcxActivationKeysClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List HCX activation keys in a VMware Engine private cloud.
          """,
    'EXAMPLES':
        """
          To list HCX activation keys in the `my-private-cloud` private cloud run:

            $ {command} --location=us-west2-a --project=my-project --private-cloud=my-private-cloud

            Or:

            $ {command} --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List HCX activation keys in a Google Cloud VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=LOCATION,'
                                  'name.segment(-3):label=PRIVATE_CLOUD,'
                                  'createTime,state,activationKey)')

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = HcxActivationKeysClient()
    return client.List(privatecloud)
