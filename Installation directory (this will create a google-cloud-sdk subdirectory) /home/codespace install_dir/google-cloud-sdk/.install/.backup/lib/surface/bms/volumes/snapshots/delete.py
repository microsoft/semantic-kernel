# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'Bare Metal Solution boot volume snapshot delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a Bare Metal Solution boot volume snapshot.
        """,
    'EXAMPLES':
        """
          To delete a snapshot called ``my-snapshot'' on boot volume
          ``my-boot-volume'' in region ``us-central1'', run:

          $ {command} my-snapshot --region=us-central1 --volume=my-boot-volume
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Bare Metal Solution boot volume snapshot."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddVolumeSnapshotArgToParser(parser, positional=True)

  def Run(self, args):
    snapshot = args.CONCEPTS.snapshot.Parse()
    client = BmsClient()
    snapshot_type = client.GetVolumeSnapshot(snapshot).type
    if snapshot_type == client.messages.VolumeSnapshot.TypeValueValuesEnum.SCHEDULED:
      console_io.PromptContinue(
          message='Deleting a SCHEDULED snapshot of a boot volume '
          'is unsafe and should only be done when necessary.',
          prompt_string='Are you sure you want to delete snapshot {}'
          .format(snapshot.Name()),
          cancel_on_no=True)
    else:
      console_io.PromptContinue(
          message=('You are about to delete the snapshot '
                   '[{0}]'.format(snapshot.Name())),
          cancel_on_no=True)
    res = client.DeleteVolumeSnapshot(snapshot)
    log.DeletedResource(snapshot.Name(), 'snapshot')
    return res


Delete.detailed_help = DETAILED_HELP
