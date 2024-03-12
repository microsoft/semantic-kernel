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
"""The 'gcloud firebase test ip-blocks list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List all IP address blocks used by Firebase Test Lab devices."""

  detailed_help = {
      'DESCRIPTION':
          """List all IP address blocks used by Firebase Test Lab
devices.""",
      'EXAMPLES':
          """To list all IP address blocks, run:

  $ {command}

To list only the CIDR blocks one per line, run:

  $ {command} --format="value(BLOCK)"
"""
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparse parser used to add arguments that follow this
          command in the CLI. Positional arguments are allowed.
    """
    parser.display_info.AddFormat("""
        table[box](
          block,
          form.color(blue=VIRTUAL,yellow=PHYSICAL),
          addedDate.date('%Y-%m-%d')
        )
    """)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run the 'gcloud firebase test ip-blocks list' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The list of IP blocks we want to have printed later.
    """
    device_ip_block_catalog = util.GetDeviceIpBlocks(self.context)
    return device_ip_block_catalog.ipBlocks
