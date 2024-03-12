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
"""Lists Cloud NetApp Volumes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes import client as volumes_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.volumes import flags as volumes_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Cloud NetApp Volumes."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Lists Cloud NetApp Volumes
          """,
      'EXAMPLES': """\
          The following command lists all Volumes in the given location

              $ {command} --location=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetResourceListingLocationPresentationSpec(
            'The location in which to list Volumes.')
    ]).AddToParser(parser)
    parser.display_info.AddFormat(volumes_flags.VOLUMES_LIST_FORMAT)

  def Run(self, args):
    """Run the list command."""
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()
    location_ref = args.CONCEPTS.location.Parse().RelativeName()
    # Default to listing all Cloud NetApp Volumes in all locations.
    location = args.location if args.location else '-'
    location_list = location_ref.split('/')
    location_list[-1] = location
    location_ref = '/'.join(location_list)
    client = volumes_client.VolumesClient(release_track=self._RELEASE_TRACK)
    # TODO(b/294604013): Re-assess whether to keep or remove args.limit to be
    # passed into List
    return list(client.ListVolumes(location_ref, limit=args.limit))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Cloud NetApp Volumes."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Lists Cloud NetApp Volumes
          """,
      'EXAMPLES': """\
          The following command lists all Volumes in the given location

              $ {command} --location=us-central1
          """,
  }


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Cloud NetApp Volumes."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

