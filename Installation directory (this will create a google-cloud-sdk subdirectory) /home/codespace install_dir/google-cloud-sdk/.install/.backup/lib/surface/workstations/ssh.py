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
"""Command for SSHing into a started workstation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import threading

from googlecloudsdk.api_lib.workstations import workstations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workstations import flags as workstations_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Start(base.Command):
  """SSH into a running workstation.

  SSH into a running workstation.

  ## EXAMPLES

    To ssh into a running workstation, run:

      $ {command} WORKSTATION

    To specify the workstation port, run:

      $ {command} WORKSTATION --port=22

    To ssh into a running workstation with a username, run:

      $ {command} WORKSTATION --user=my-user

    To run a command on the workstation, such as getting a snapshot of the
    guest's process tree, run:
      $ {command} WORKSTATION --command="ps -ejH"
  """

  @staticmethod
  def Args(parser):
    workstations_flags.AddWorkstationResourceArg(parser)
    workstations_flags.AddPortField(parser)
    workstations_flags.AddLocalHostPortField(parser)
    workstations_flags.AddCommandField(parser)
    workstations_flags.AddSshArgsAndUserField(parser)

  def Collection(self):
    return 'workstations.projects.locations.workstationClusters.workstationConfigs.workstations'

  def Run(self, args):
    # Format arguments for StartTcpTunnel
    args.workstation_port = args.port

    client = workstations.Workstations(self.ReleaseTrack())

    client.threading_event.clear()
    client.tcp_tunnel_open = False

    t = threading.Thread(target=client.StartTcpTunnel, args=(args, True))
    t.daemon = True
    t.start()

    client.threading_event.wait()
    if client.tcp_tunnel_open:
      client.Ssh(args)
