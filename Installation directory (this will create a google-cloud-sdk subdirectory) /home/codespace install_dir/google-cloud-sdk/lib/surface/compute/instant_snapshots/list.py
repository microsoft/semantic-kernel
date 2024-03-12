# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""List instant snapshot command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.instant_snapshots import flags as ips_flags


def _CommonArgs(parser):
  parser.display_info.AddFormat(ips_flags.MULTISCOPE_LIST_FORMAT)
  parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
  lister.AddMultiScopeListerFlags(parser, zonal=True, regional=True)
  parser.display_info.AddCacheUpdater(completers.InstantSnapshotsCompleter)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine persistent instant snapshots."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.instantSnapshots,
        regional_service=client.apitools_client.regionInstantSnapshots,
        aggregation_service=client.apitools_client.instantSnapshots)

    return lister.Invoke(request_data, list_implementation)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Compute Engine persistent instant snapshots in beta."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Compute Engine persistent instant snapshots in alpha."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


List.detailed_help = base_classes.GetMultiScopeListerHelp(
    'instant snapshots',
    scopes=[
        base_classes.ScopeType.zonal_scope,
        base_classes.ScopeType.regional_scope,
    ],
)
