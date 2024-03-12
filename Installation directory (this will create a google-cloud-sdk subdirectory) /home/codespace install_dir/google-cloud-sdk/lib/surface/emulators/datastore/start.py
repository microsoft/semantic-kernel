# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""gcloud datastore emulator start command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import socket
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import datastore_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Start(base.Command):
  """Start a local datastore emulator.

  This command starts a local datastore emulator.
  """

  detailed_help = {
      'EXAMPLES': """
To start a local datastore emulator, run:

  $ {command} --data-dir=DATA-DIR
""",
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--host-port',
        required=False,
        type=lambda arg: arg_parsers.HostPort.Parse(arg, ipv6_enabled=True),
        help='The host:port to which the emulator should be bound. Can '
        'take the form of a single address (hostname, IPv4, or IPv6) and/or '
        'port:\n\n  [ADDRESS][:PORT]\n\n'
        'In this format you must enclose IPv6 addresses in square brackets: '
        'e.g.\n\n'
        '  [2001:db8:0:0:0:ff00:42:8329]:8080\n\n'
        'The default value is localhost:8081.')
    parser.add_argument(
        '--store-on-disk',
        default=True,
        action='store_true',
        help='Whether data should be persisted to disk.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--consistency',
        required=False,
        type=float,
        default=0.9,
        help='Fraction of eventually consistent operations that '
             'should succeed immediately. Setting to 1.0 can be useful '
             'for unit tests, but may mask incorrect assumptions about '
             'non-ancestor queries which are eventually consistent.')
    group.add_argument(
        '--use-firestore-in-datastore-mode',
        default=False,
        action='store_true',
        help='Runs the emulator in Cloud Firestore in Datastore Mode. '
        'Reads are always strongly consistent and --consistency flag may not '
        'be specified.')

  def Run(self, args):
    if not args.host_port:
      args.host_port = arg_parsers.HostPort.Parse(
          datastore_util.GetHostPort(), ipv6_enabled=socket.has_ipv6)
    args.host_port.host = args.host_port.host or 'localhost'
    args.host_port.port = args.host_port.port or '8081'

    java.RequireJavaInstalled(datastore_util.DATASTORE_TITLE, min_version=11)
    datastore_util.PrepareGCDDataDir(args)
    with datastore_util.StartGCDEmulator(args) as proc:
      datastore_util.WriteGCDEnvYaml(args)
      util.PrefixOutput(proc, 'datastore')
