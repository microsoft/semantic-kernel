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
"""Command for describing Cloud NetApp Files locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp import netapp_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Cloud NetApp Files location."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION':
          'Describe a Cloud NetApp Files location.',
      'EXAMPLES':
          """\
            The following command shows the details for the NetApp Files location named NAME.

                $ {command} NAME
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetLocationPresentationSpec('The location to describe.')
    ]).AddToParser(parser)

  def Run(self, args):
    """Run the describe command."""
    location_ref = args.CONCEPTS.location.Parse().RelativeName()
    client = netapp_client.NetAppClient(release_track=self._RELEASE_TRACK)
    return client.GetLocation(location_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describe a Cloud NetApp Files location."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeBeta):
  """Describe a Cloud NetApp Files location."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

