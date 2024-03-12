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
"""gcloud bigtable emulator start command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import bigtable_util
from googlecloudsdk.command_lib.emulators import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Start(base.Command):
  """Start a local Bigtable emulator.

  This command starts a local Bigtable emulator.
  """

  detailed_help = {
      'EXAMPLES': """\
          To start a local Bigtable emulator, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--host-port',
        required=False,
        type=lambda arg: arg_parsers.HostPort.Parse(arg, ipv6_enabled=True),
        help='The host:port to which the emulator should be bound. The default '
        'value is localhost:8086.')

  # Override
  def Run(self, args):
    if not args.host_port:
      args.host_port = arg_parsers.HostPort.Parse(util.GetHostPort(
          bigtable_util.BIGTABLE), ipv6_enabled=True)

    bigtable_util.Start(args)
