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
"""Delete a Cloud NetApp Volume Snapshot."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.snapshots import client as snapshots_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.netapp.volumes.snapshots import flags as snapshots_flags

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Delete a Cloud NetApp Volume Snapshot.
          """,
      'EXAMPLES': """\
          The following command deletes a Snapshot named NAME in the given location and volume:

              $ {command} NAME --location=us-central1 --volume=vol1

          To delete a Snapshot named NAME asynchronously, run the following command:

              $ {command} NAME --location=us-central1 --volume=vol1 --async
          """,
  }

  @staticmethod
  def Args(parser):
    snapshots_flags.AddSnapshotDeleteArgs(parser)

  def Run(self, args):
    """Delete a Cloud NetApp Volume Snapshot in the current project."""
    snapshot_ref = args.CONCEPTS.snapshot.Parse()

    if args.CONCEPTS.volume.Parse() is None:
      raise exceptions.RequiredArgumentException(
          '--volume', 'Requires a volume to delete snapshot of')

    if not args.quiet:
      delete_warning = ('You are about to delete a Snapshot {}.\n'
                        'Are you sure?'.format(snapshot_ref.RelativeName()))
      if not console_io.PromptContinue(message=delete_warning):
        return None

    client = snapshots_client.SnapshotsClient(self._RELEASE_TRACK)
    result = client.DeleteSnapshot(snapshot_ref, args.async_)
    if args.async_:
      command = 'gcloud {} netapp volumes snapshots list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the deletion by listing all snapshots:\n  '
          '$ {} '.format(command))
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(DeleteBeta):
  """Delete a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

