# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""The 'gcloud firebase test ip-blocks' sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class IpBlocks(base.Group):
  """Explore IP blocks used by Firebase Test Lab devices."""

  detailed_help = {
      'DESCRIPTION':
          """
          Get a list of IP address blocks in CIDR notation used by Firebase Test
          Lab devices.
          """,
      'EXAMPLES':
          """
          To see the list of the IP blocks used, their form factors, and
          the date they were added to Firebase Test Lab, run:

            $ {command} list
      """
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags common to this sub-group.

    Args:
      parser: An argparse parser used to add arguments that immediately follow
          this group in the CLI. Positional arguments are allowed.
    """
    pass
