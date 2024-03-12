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
"""Stop a Cloud NetApp Volume Replication."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.replications import client as replications_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.volumes.replications import flags as replications_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Stop(base.Command):
  """Stop a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Stop a Cloud NetApp Volume Replication.
          """,
      'EXAMPLES': """\
          The following command stops a Replication named NAME using the required arguments:

              $ {command} NAME --location=us-central1 --volume=vol1

          To stop a Replication named NAME asynchronously, run the following command:

              $ {command} NAME --location=us-central1 --volume=vol1 --async
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [flags.GetReplicationPresentationSpec('The Replication to create.')]
    ).AddToParser(parser)
    replications_flags.AddReplicationVolumeArg(parser)
    flags.AddResourceAsyncFlag(parser)
    replications_flags.AddReplicationForceArg(parser)

  def Run(self, args):
    """Stop a Cloud NetApp Volume Replication in the current project."""
    replication_ref = args.CONCEPTS.replication.Parse()

    client = replications_client.ReplicationsClient(self._RELEASE_TRACK)
    result = client.StopReplication(
        replication_ref, args.async_, args.force)
    if args.async_:
      command = 'gcloud {} netapp volumes replications list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the stopped replication by listing all'
          ' replications:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class StopBeta(Stop):
  """Stop a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA
