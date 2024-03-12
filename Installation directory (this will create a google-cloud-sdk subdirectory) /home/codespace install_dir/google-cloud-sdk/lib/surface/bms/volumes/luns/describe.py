# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'Bare Metal Solution LUNs describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a Bare Metal Solution logical unit number (LUN).
        """,
    'EXAMPLES':
        """
          To get details about a LUN called ``my-lun'' on volume ``my-volume''
          in region ``us-central1'', run:

          $ {command} my-lun --region=us-central1 --volume=my-volume
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Bare Metal Solution LUN."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLunArgToParser(parser)

  def Run(self, args):
    lun = args.CONCEPTS.lun.Parse()
    client = BmsClient()
    return client.GetLUN(lun)


Describe.detailed_help = DETAILED_HELP
