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
"""Create a Cloud NetApp Volume Snapshot."""

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
class Create(base.CreateCommand):
  """Create a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Create a Cloud NetApp Volume Snapshot.
          """,
      'EXAMPLES': """\
          The following command creates a Snapshot named NAME using the required arguments:

              $ {command} NAME --location=us-central1 --volume=vol1
          """,
  }

  @staticmethod
  def Args(parser):
    snapshots_flags.AddSnapshotCreateArgs(parser)

  def Run(self, args):
    """Create a Cloud NetApp Volume Snapshot in the current project."""
    snapshot_ref = args.CONCEPTS.snapshot.Parse()

    if args.CONCEPTS.volume.Parse() is None:
      raise exceptions.RequiredArgumentException(
          '--volume', 'Requires a volume to create snapshot of'
      )

    volume_ref = args.CONCEPTS.volume.Parse().RelativeName()
    client = snapshots_client.SnapshotsClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.Snapshot.LabelsValue
    )

    snapshot = client.ParseSnapshotConfig(
        name=snapshot_ref.RelativeName(),
        description=args.description,
        labels=labels,
    )
    result = client.CreateSnapshot(
        snapshot_ref, volume_ref, args.async_, snapshot
    )
    if args.async_:
      command = 'gcloud {} netapp volumes snapshots list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new snapshot by listing all snapshots:\n  '
          '$ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Creates a Cloud NetApp Volume Snapshot."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

