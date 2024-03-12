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
"""Command for spanner SSD caches list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import ssd_caches
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags


class List(base.ListCommand):
  """List available Cloud Spanner SSD caches."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
        To list the Cloud Spanner SSD caches in an instance config, run:

          $ {command} --config=my-config-id
        """),
  }

  @staticmethod
  def Args(parser):
    flags.Config().AddToParser(parser)
    base.FILTER_FLAG.RemoveFromParser(parser)  # we don't support filter
    parser.display_info.AddFormat("""
          table(
            name.basename(),
            displayName,
            size_gib,
            labels
          )
        """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    return ssd_caches.List(args.config)
