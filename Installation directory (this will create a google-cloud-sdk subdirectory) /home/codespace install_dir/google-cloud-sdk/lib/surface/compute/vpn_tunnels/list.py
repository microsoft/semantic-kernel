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
"""Command for listing VPN tunnels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute.vpn_tunnels import vpn_tunnels_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.vpn_tunnels import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projection_spec


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ListBetaGA(base.ListCommand):
  """List VPN tunnels."""

  # Placeholder to indicate that a detailed_help field exists and should
  # be set outside the class definition.
  detailed_help = None

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    lister.AddRegionsArg(parser)
    parser.display_info.AddCacheUpdater(flags.VpnTunnelsCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = vpn_tunnels_utils.VpnTunnelHelper(holder)

    project = properties.VALUES.core.project.GetOrFail()
    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    args.filter, filter_expr = filter_rewrite.Rewriter().Rewrite(
        args.filter, defaults=defaults)
    return helper.List(project=project, filter_expr=filter_expr)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBetaGA):
  """List VPN tunnels."""

  @staticmethod
  def Args(parser):
    ListBetaGA.Args(parser)
    parser.display_info.AddFormat(flags.HA_VPN_LIST_FORMAT)


ListBetaGA.detailed_help = base_classes.GetRegionalListerHelp('VPN tunnels')
ListAlpha.detailed_help = ListBetaGA.detailed_help
