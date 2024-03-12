# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for listing disk types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine disk types."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          zone.basename(),
          validDiskSize:label=VALID_DISK_SIZES
        )""")
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    lister.AddZonalListerArgs(parser)
    parser.display_info.AddCacheUpdater(completers.DiskTypesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseZonalFlags(args, holder.resources)

    list_implementation = lister.ZonalLister(
        client, client.apitools_client.diskTypes)

    return lister.Invoke(request_data, list_implementation)


def _AddAlphaBetaCommonArgs(parser):
  """Add args and flags that are common to ALPHA and BETA tracks."""

  parser.add_argument(
      'names',
      metavar='NAME',
      nargs='*',
      default=[],
      completer=completers.DiskTypesCompleter,
      help=('If provided, show details for the specified names and/or URIs '
            'of resources.'))
  parser.add_argument(
      '--regexp', '-r',
      help="""\
      A regular expression to filter the names of the results on. Any names
      that do not match the entire regular expression will be filtered out.
      """)
  parser.display_info.AddCacheUpdater(completers.DiskTypesCompleter)

  scope = parser.add_mutually_exclusive_group()
  scope.add_argument(
      '--zones',
      metavar='ZONE',
      help=('If provided, only zonal resources are shown. '
            'If arguments are provided, only resources from the given '
            'zones are shown.'),
      type=arg_parsers.ArgList())
  scope.add_argument(
      '--regions',
      metavar='REGION',
      help=('If provided, only regional resources are shown. '
            'If arguments are provided, only resources from the given '
            'regions are shown.'),
      type=arg_parsers.ArgList())

  parser.display_info.AddFormat("""
        table(
          name,
          location():label=LOCATION,
          location_scope():label=SCOPE,
          validDiskSize:label=VALID_DISK_SIZES
        )
  """)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """List Compute Engine disk types."""

  SCOPES = (base_classes.ScopeType.regional_scope,
            base_classes.ScopeType.zonal_scope)

  @staticmethod
  def Args(parser):
    _AddAlphaBetaCommonArgs(parser)

  def _GetFilter(self, names, name_regex, zones, regions):
    result = []
    if names:
      result.append('(name eq {0})'.format('|'.join(names)))
    if name_regex:
      result.append('(name eq {0})'.format(name_regex))
    if zones:
      result.append('(zone eq {0})'.format('|'.join(zones)))
    if regions:
      result.append('(region eq {0})'.format('|'.join(regions)))
    return ''.join(result) or None

  def Run(self, args):
    api_version = self.ReleaseTrack().prefix
    compute_disk_types = apis.GetClientInstance('compute',
                                                api_version).diskTypes
    messages = apis.GetMessagesModule('compute', api_version)

    request = messages.ComputeDiskTypesAggregatedListRequest(
        filter=self._GetFilter(
            args.names, args.regexp, args.zones, args.regions),
        project=properties.VALUES.core.project.Get(required=True),
    )

    # TODO(b/34871930): Write and use helper for handling listing.
    return utils.GetListPager(
        compute_disk_types, request, lambda r: r.value.diskTypes)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):

  @staticmethod
  def Args(parser):
    _AddAlphaBetaCommonArgs(parser)
    parser.display_info.AddCacheUpdater(completers.DiskTypesCompleter)

List.detailed_help = base_classes.GetZonalListerHelp('disk types')
ListBeta.detailed_help = base_classes.GetMultiScopeListerHelp(
    'disk types', ListBeta.SCOPES)
ListAlpha.detailed_help = base_classes.GetMultiScopeListerHelp(
    'disk types', ListAlpha.SCOPES)
