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
"""Command for listing Cloud NetApp Files operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp import netapp_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.operations import flags as operations_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Cloud NetApp Files operations."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION':
          'Lists all Cloud NetApp Files operations.',
      'EXAMPLES':
          """\
            The following command lists NetApp Files operations under a given location

                $ {command} --location=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetResourceListingLocationPresentationSpec(
            'The location in which to list operations.')
    ]).AddToParser(parser)
    parser.display_info.AddFormat(operations_flags.OPERATIONS_LIST_FORMAT)

  def Run(self, args):
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()

    location_ref = args.CONCEPTS.location.Parse().RelativeName()
    if args.location:
      location_list = location_ref.split('/')
      location_list[-1] = args.location
      location_ref = '/'.join(location_list)
    client = netapp_client.NetAppClient(release_track=self._RELEASE_TRACK)
    return list(client.ListOperations(location_ref, limit=args.limit))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Cloud NetApp Files operations."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION':
          'Lists all Cloud NetApp Files operations.',
      'EXAMPLES':
          """\
            The following command lists NetApp Files operations under a given location

                $ {command} --location=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetResourceListingLocationPresentationSpec(
            'The location in which to list operations.')
    ]).AddToParser(parser)
    parser.display_info.AddFormat(operations_flags.OPERATIONS_LIST_FORMAT)

  def Run(self, args):
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()

    location_ref = args.CONCEPTS.location.Parse().RelativeName()
    if args.location:
      location_list = location_ref.split('/')
      location_list[-1] = args.location
      location_ref = '/'.join(location_list)
    client = netapp_client.NetAppClient(release_track=self._RELEASE_TRACK)
    return list(client.ListOperations(location_ref, limit=args.limit))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Cloud NetApp Files operations."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

