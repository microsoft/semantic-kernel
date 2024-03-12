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
"""gcloud pubsub emulator start command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import pubsub_util
from googlecloudsdk.command_lib.emulators import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Start(base.Command):
  """Start a local pubsub emulator.

  This command starts a local pubsub emulator.

  On successful start up, you should expect to see:

  ```
  ...
  [pubsub] This is the Google Pub/Sub fake.
  [pubsub] Implementation may be incomplete or differ from the real system.
  ...
  [pubsub] INFO: Server started, listening on 8538
  ```
  """

  detailed_help = {
      'EXAMPLES': """
To start a local pubsub emulator, run:

  $ {command} --data-dir=DATA-DIR
""",
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--host-port',
        required=False,
        type=lambda arg: arg_parsers.HostPort.Parse(arg, ipv6_enabled=True),
        help='The host:port to which the emulator should be bound. The default '
             'value is [::1]:8085.')

  # Override
  def Run(self, args):
    if not args.host_port:
      args.host_port = arg_parsers.HostPort.Parse(util.GetHostPort(
          pubsub_util.PUBSUB), ipv6_enabled=True)

    with pubsub_util.Start(args) as pubsub_process:
      util.WriteEnvYaml(pubsub_util.GetEnv(args), args.data_dir)
      util.PrefixOutput(pubsub_process, pubsub_util.PUBSUB)
