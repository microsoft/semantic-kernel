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
"""Command for listing Cloud NetApp Files locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp import netapp_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.locations import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List all Cloud NetApp Files locations."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION':
          'Lists all Cloud NetApp Files locations.',
      'EXAMPLES':
          """\
            The following command lists NetApp Files locations.

                $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.LOCATIONS_LIST_FORMAT)

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.GetOrFail(),
        collection='netapp.projects')
    client = netapp_client.NetAppClient(release_track=self._RELEASE_TRACK)
    return list(client.ListLocations(project_ref, limit=args.limit))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List all Cloud NetApp Files locations."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List all Cloud NetApp Files locations."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

