# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Command for listing Filestore instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.filestore import flags
from googlecloudsdk.command_lib.filestore.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Filestore instances."""

  _API_VERSION = filestore_client.V1_API_VERSION

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([flags.GetListingLocationPresentationSpec(
        'The location in which to list instances.')]).AddToParser(parser)
    instances_flags.AddLocationArg(parser)
    instances_flags.AddRegionArg(parser)
    parser.display_info.AddFormat(instances_flags.INSTANCES_LIST_FORMAT)

    def UriFunc(resource):
      registry = filestore_client.GetFilestoreRegistry()
      ref = registry.Parse(
          resource.name, collection=filestore_client.INSTANCES_COLLECTION)
      return ref.SelfLink()

    parser.display_info.AddUriFunc(UriFunc)

  def Run(self, args):
    """Run the list command."""
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()

    location_ref = args.CONCEPTS.zone.Parse().RelativeName()
    if args.zone is None and args.location is not None:
      location_list = location_ref.split('/')
      location_list[-1] = args.location
      location_ref = '/'.join(location_list)
    client = filestore_client.FilestoreClient(version=self._API_VERSION)
    return list(client.ListInstances(location_ref, limit=args.limit))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Filestore instances."""

  _API_VERSION = filestore_client.BETA_API_VERSION

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetListingLocationPresentationSpec(
            'The location in which to list instances.')
    ]).AddToParser(parser)
    instances_flags.AddLocationArg(parser)
    instances_flags.AddRegionArg(parser)
    parser.display_info.AddFormat(instances_flags.INSTANCES_LIST_FORMAT_BETA)

    def UriFunc(resource):
      registry = filestore_client.GetFilestoreRegistry(
          filestore_client.BETA_API_VERSION)
      ref = registry.Parse(
          resource.name, collection=filestore_client.INSTANCES_COLLECTION)
      return ref.SelfLink()

    parser.display_info.AddUriFunc(UriFunc)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Filestore instances."""

  _API_VERSION = filestore_client.ALPHA_API_VERSION

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([flags.GetListingLocationPresentationSpec(
        'The location in which to list instances.')]).AddToParser(parser)
    instances_flags.AddLocationArg(parser)
    instances_flags.AddRegionArg(parser)
    parser.display_info.AddFormat(instances_flags.INSTANCES_LIST_FORMAT)

    def UriFunc(resource):
      registry = resources.REGISTRY.Clone()
      registry.RegisterApiByName(
          filestore_client.API_NAME,
          api_version=filestore_client.ALPHA_API_VERSION)
      ref = registry.Parse(
          resource.name, collection=filestore_client.INSTANCES_COLLECTION)
      return ref.SelfLink()

    parser.display_info.AddUriFunc(UriFunc)

  def Run(self, args):
    """Run the list command."""
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()
    location_ref = args.CONCEPTS.zone.Parse().RelativeName()
    # Fetch the location value from fallback options when args.zone is absent.
    # The fallback options will check args.region first, then args.location if
    # args.region also absent.
    if args.zone is None:
      location_list = location_ref.split('/')
      if args.region is not None:
        location_list[-1] = args.region
      elif args.location is not None:
        location_list[-1] = args.location
      location_ref = '/'.join(location_list)
    client = filestore_client.FilestoreClient(version=self._API_VERSION)
    return list(client.ListInstances(location_ref, limit=args.limit))


List.detailed_help = {
    'DESCRIPTION':
        '',
    'EXAMPLES':
        """\
The following command lists a maximum of five Filestore instances sorted
alphabetically by name in descending order:

  $ {command} --limit=5 --sort-by=~name
"""
}
