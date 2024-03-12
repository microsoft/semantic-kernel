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
"""List Cloud NetApp Volume Snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.snapshots import client as snapshots_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.volumes.snapshots import flags as snapshots_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers

from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Cloud NetApp Volume Snapshots."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Lists Cloud NetApp Volume Snapshots.
          """,
      'EXAMPLES': """\
          The following command lists all Snapshots in the given location and volume:

              $ {command} --location=us-central1 --volume=vol1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetResourceListingLocationPresentationSpec(
            'The location in which to list Volume Snapshots.')
    ]).AddToParser(parser)
    snapshots_flags.AddSnapshotVolumeArg(parser)

  def Run(self, args):
    """Run the list command."""
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()

    if args.CONCEPTS.volume.Parse() is None:
      raise exceptions.RequiredArgumentException(
          '--volume', 'Requires a volume to list snapshots of')

    volume_ref = args.CONCEPTS.volume.Parse().RelativeName()
    client = snapshots_client.SnapshotsClient(release_track=self._RELEASE_TRACK)
    return list(client.ListSnapshots(volume_ref, limit=args.limit))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Cloud NetApp Volume Snapshots."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Cloud NetApp Volume Snapshots."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

