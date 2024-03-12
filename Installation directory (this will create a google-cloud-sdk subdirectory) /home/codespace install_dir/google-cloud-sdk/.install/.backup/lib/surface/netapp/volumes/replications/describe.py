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
"""Describe a Cloud NetApp Volume Replication."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.replications import client as replications_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.volumes.replications import flags as replications_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Describe a Cloud NetApp Volume Replication.
          """,
      'EXAMPLES': """\
          The following command describes a Replication named NAME in the given location and volume:

              $ {command} NAME --location=us-central1 --volume=vol1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [flags.GetReplicationPresentationSpec('The Replication to describe.')]
    ).AddToParser(parser)
    replications_flags.AddReplicationVolumeArg(parser)

  def Run(self, args):
    """Get a Cloud NetApp Volume Replication in the current project."""
    replication_ref = args.CONCEPTS.replication.Parse()

    client = replications_client.ReplicationsClient(
        release_track=self._RELEASE_TRACK
    )
    return client.GetReplication(replication_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describe a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Describe a Cloud NetApp Volume Replication
          """,
      'EXAMPLES': """\
          The following command describes a Replication named NAME in the given location and volume

              $ {command} NAME --location=us-central1 --volume=vol1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [flags.GetReplicationPresentationSpec('The Replication to describe.')]
    ).AddToParser(parser)
    replications_flags.AddReplicationVolumeArg(parser)

  def Run(self, args):
    """Get a Cloud NetApp Volume Replication in the current project."""
    replication_ref = args.CONCEPTS.replication.Parse()

    client = replications_client.ReplicationsClient(
        release_track=self._RELEASE_TRACK
    )
    return client.GetReplication(replication_ref)
