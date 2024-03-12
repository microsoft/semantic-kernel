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
"""Command for spanner instances get-locations."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import textwrap
from googlecloudsdk.api_lib.spanner import instances
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class AlphaMove(base.Command):
  """Moves the instance to the specified instance config."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
        To move the Cloud Spanner instance to the target instance configuration, run:
          $ {command} my-instance-id --target-config=nam3
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    For `move` command, we have one positional argument, `instanceId`

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.Instance().AddToParser(parser)
    flags.TargetConfig().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. From `Args`, we extract command line
        arguments
    """
    instances.Move(args.instance, args.target_config)
