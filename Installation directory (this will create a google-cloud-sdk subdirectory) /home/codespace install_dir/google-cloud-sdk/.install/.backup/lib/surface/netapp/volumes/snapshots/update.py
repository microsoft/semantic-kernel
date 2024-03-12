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
"""Update a Cloud NetApp Volume Snapshot."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.snapshots import client as snapshots_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.netapp.volumes.snapshots import flags as snapshots_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Update a Cloud NetApp Volume Snapshot and its specified parameters.
          """,
      'EXAMPLES': """\
          The following command updates a Snapshot named NAME and its specified parameters:

              $ {command} NAME --location=us-central1 --description="new" --update-labels=key2=val2 --volume=vol1
          """,
  }

  @staticmethod
  def Args(parser):
    snapshots_flags.AddSnapshotUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Volume Snapshot in the current project."""
    snapshot_ref = args.CONCEPTS.snapshot.Parse()

    if args.CONCEPTS.volume.Parse() is None:
      raise exceptions.RequiredArgumentException(
          '--volume', 'Requires a volume to update snapshot of')

    client = snapshots_client.SnapshotsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    original_snapshot = client.GetSnapshot(snapshot_ref)

    # Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.Snapshot.LabelsValue, original_snapshot.labels
      ).GetOrNone()
    else:
      labels = None

    snapshot = client.ParseUpdatedSnapshotConfig(
        original_snapshot, description=args.description, labels=labels
    )

    updated_fields = []
    # add possible updated snapshot fields
    # TODO(b/243601146) add config mapping and separate config file for update
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateSnapshot(
        snapshot_ref, snapshot, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp volumes snapshots list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated snapshot by listing all snapshots:\n'
          '  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
