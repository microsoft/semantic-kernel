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
"""Describes a Cloud NetApp Volume."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes import client as volumes_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Show metadata for a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Describe a Cloud NetApp Volume
          """,
      'EXAMPLES': """\
          The following command describe a Volume named NAME in the given location

              $ {command} NAME --location=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([flags.GetVolumePresentationSpec(
        'The Volume to describe.')]).AddToParser(parser)

  def Run(self, args):
    """Run the describe command."""
    volume_ref = args.CONCEPTS.volume.Parse()
    client = volumes_client.VolumesClient(release_track=self._RELEASE_TRACK)
    return client.GetVolume(volume_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Show metadata for a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeBeta):
  """Show metadata for a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

