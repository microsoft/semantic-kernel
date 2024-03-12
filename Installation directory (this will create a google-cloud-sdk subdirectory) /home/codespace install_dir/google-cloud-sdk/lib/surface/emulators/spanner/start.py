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
"""gcloud emulators spanner start command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import spanner_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Start(base.Command):
  """Start a local Cloud Spanner emulator.

  This command starts a local Cloud Spanner emulator.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To start a local Cloud Spanner emulator, run:

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
        'value is localhost:9010. Note that this port serves gRPC requests. To '
        'override the default port serving REST requests, use --rest-port. If '
        'using Docker to run the emulator, the host must be specified as an '
        'ipaddress.')
    parser.add_argument(
        '--rest-port',
        required=False,
        type=arg_parsers.BoundedInt(1, 65535),
        help='The port at which REST requests are served. gcloud uses REST to '
        'communicate with the emulator. The default value is 9020.')
    parser.add_argument(
        '--use-docker',
        required=False,
        type=arg_parsers.ArgBoolean(),
        help='Use the Cloud Spanner emulator docker image even if the platform '
        'has a native binary available in the gcloud CLI. Currently we only '
        'provide a native binary for Linux. For other systems, you must '
        'install Docker for your platform before starting the emulator.')
    parser.add_argument(
        '--enable-fault-injection',
        required=False,
        type=arg_parsers.ArgBoolean(),
        help='If true, the emulator will randomly inject faults into '
        'transactions. This facilitates application abort-retry testing.',
        default=False)

  def Run(self, args):
    if not args.host_port:
      args.host_port = arg_parsers.HostPort('localhost', '9010')
    if not args.rest_port:
      args.rest_port = 9020

    spanner_util.Start(args)
