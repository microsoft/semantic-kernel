# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The 'gcloud firebase test network-profiles list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List all network profiles available for testing."""

  detailed_help = {
      'DESCRIPTION': """List all network profiles available for testing.

Run `$ {parent_command} --help` for descriptions of the network profile
parameters.
""",
      'EXAMPLES': """To list all network profiles, run:

  {command}

To list all GSM network profiles, run:

  {command} --filter="id:GSM"
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
            id:label=PROFILE_ID,
            synthesize((rule:up, upRule),(rule:down, downRule)):
              format="table[box](
                rule,
                delay,
                packetLossRatio:label=LOSS_RATIO,
                packetDuplicationRatio:label=DUPLICATION_RATIO,
                bandwidth,
                burst
              )"
          )
    """)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run the 'gcloud firebase test network-profiles list' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The list of network profiles we want to have printed later or None.
    """
    catalog = util.GetNetworkProfileCatalog(self.context)
    return getattr(catalog, 'configurations', None)
