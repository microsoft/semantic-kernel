# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for deleting packet mirroring resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils

from googlecloudsdk.calliope import base

from googlecloudsdk.command_lib.compute.packet_mirrorings import client
from googlecloudsdk.command_lib.compute.packet_mirrorings import flags


class Delete(base.DeleteCommand):
  """Delete a Compute Engine packet mirroring policy."""

  PACKET_MIRRORING_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.PACKET_MIRRORING_ARG = flags.PacketMirroringArgument(plural=True)
    cls.PACKET_MIRRORING_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.PacketMirroringCompleter)

  def Collection(self):
    return 'compute.packetMirrorings'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    refs = self.PACKET_MIRRORING_ARG.ResolveAsResource(args, holder.resources)
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      packet_mirroring = client.PacketMirroring(
          ref, compute_client=holder.client)
      requests.append(packet_mirroring.MakeDeleteRequestTuple())
    return holder.client.MakeRequests(requests)

Delete.detailed_help = {
    'DESCRIPTION': 'Delete a Compute Engine Packet Mirroring policy.',
    'EXAMPLES':
    """\
    Delete the Packet Mirroring policy pm-1 in region us-central1.

      $ {command} pm-1
        --region us-central1
    """
}
