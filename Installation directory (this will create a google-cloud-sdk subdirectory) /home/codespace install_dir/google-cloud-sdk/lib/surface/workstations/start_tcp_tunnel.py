# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Implements a command to forward TCP traffic to a workstation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workstations import workstations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workstations import flags as workstations_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class StartTcpTunnel(base.Command):
  """Start a tunnel through which a local process can forward TCP traffic to the workstation."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To start a tunnel to port 22 on a workstation, run:

            $ {command} --project=my-project --region=us-central1 --cluster=my-cluster --config=my-config my-workstation 22
          """,
  }

  @staticmethod
  def Args(parser):
    workstations_flags.AddWorkstationResourceArg(parser)
    workstations_flags.AddWorkstationPortField(parser)
    workstations_flags.AddLocalHostPortField(parser)

  def Run(self, args):
    client = workstations.Workstations(self.ReleaseTrack())
    client.StartTcpTunnel(args)
