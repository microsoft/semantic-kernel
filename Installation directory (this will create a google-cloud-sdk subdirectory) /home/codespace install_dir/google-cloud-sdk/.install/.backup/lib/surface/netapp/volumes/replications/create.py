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
"""Create a Cloud NetApp Volume Replication."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.replications import client as replications_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.volumes.replications import flags as replications_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Create a Cloud NetApp Volume Replication.
          """,
      'EXAMPLES': """\
          The following command creates a Replication named NAME using the required arguments:

              $ {command} NAME --location=us-central1 --volume=vol1 --replication-schedule=EVERY_10_MINUTES --destination-volume-parameters=storage_pool=sp1,volume_id=vol2,share_name=share2
          """,
  }

  @staticmethod
  def Args(parser):
    """Add args for creating a Replication."""
    concept_parsers.ConceptParser(
        [flags.GetReplicationPresentationSpec('The Replication to create.')]
    ).AddToParser(parser)
    replications_flags.AddReplicationVolumeArg(parser)
    replications_flags.AddReplicationReplicationScheduleArg(parser)
    replications_flags.AddReplicationDestinationVolumeParametersArg(parser)
    flags.AddResourceAsyncFlag(parser)
    flags.AddResourceDescriptionArg(parser, 'Replication')
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    """Create a Cloud NetApp Volume Replication in the current project."""
    replication_ref = args.CONCEPTS.replication.Parse()

    volume_ref = args.CONCEPTS.volume.Parse().RelativeName()
    client = replications_client.ReplicationsClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.Replication.LabelsValue
    )
    replication_schedule_enum = (
        replications_flags.GetReplicationReplicationScheduleEnumFromArg(
            args.replication_schedule, client.messages
        )
    )

    replication = client.ParseReplicationConfig(
        name=replication_ref.RelativeName(),
        description=args.description,
        labels=labels,
        replication_schedule=replication_schedule_enum,
        destination_volume_parameters=args.destination_volume_parameters,
    )
    result = client.CreateReplication(
        replication_ref, volume_ref, args.async_, replication
    )
    if args.async_:
      command = 'gcloud {} netapp volumes replications list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new replication by listing all'
          ' replications:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

