# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner instance configs describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import instance_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags


class Describe(base.DescribeCommand):
  """Describe a Cloud Spanner instance configuration."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To describe an instance config named regional-us-central1, run:

          $ {command} regional-us-central1

        To describe an instance config named nam-eur-asia1, run:

          $ {command} nam-eur-asia1
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'config',
        metavar='INSTANCE_CONFIG',
        completer=flags.InstanceConfigCompleter,
        help='Cloud Spanner instance config.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    return instance_configs.Get(args.config)
