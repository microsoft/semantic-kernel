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

"""Command to show Cluster Ugprade Feature information for a Fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

import frozendict
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.clusterupgrade import flags as clusterupgrade_flags
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import times


CLUSTER_UPGRADE_FEATURE = 'clusterupgrade'


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Describe(feature_base.DescribeCommand):
  """Describe the clusterupgrade feature for a fleet within a given project."""

  detailed_help = frozendict.frozendict({
      'DESCRIPTION': """\
          Describe the Fleet clusterupgrade feature used for configuring
          fleet-based rollout sequencing.
          """,
      'EXAMPLES': """\
          To view the cluster upgrade feature information for the current fleet, run:

              $ {command}
          """,
  })

  feature_name = CLUSTER_UPGRADE_FEATURE

  @staticmethod
  def Args(parser):
    flags = clusterupgrade_flags.ClusterUpgradeFlags(parser)
    flags.AddShowLinkedClusterUpgrade()

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    feature = self.GetFeature(project=project)
    return self.GetFleetClusterUpgradeInfo(project, feature, args)

  @staticmethod
  def GetProjectIDFromFleet(fleet):
    """Extracts the project ID from the fleet."""
    return fleet

  @staticmethod
  def FormatDurations(cluster_upgrade_spec):
    """Formats display strings for all cluster upgrade duration fields."""
    if cluster_upgrade_spec.postConditions is not None:
      default_soaking = cluster_upgrade_spec.postConditions.soaking
      if default_soaking is not None:
        cluster_upgrade_spec.postConditions.soaking = Describe.DisplayDuration(
            default_soaking
        )
    for override in cluster_upgrade_spec.gkeUpgradeOverrides:
      if override.postConditions is not None:
        override_soaking = override.postConditions.soaking
        if override_soaking is not None:
          override.postConditions.soaking = Describe.DisplayDuration(
              override_soaking
          )
    return cluster_upgrade_spec

  @staticmethod
  def DisplayDuration(proto_duration_string):
    """Returns the display string for a duration value."""
    duration = times.ParseDuration(proto_duration_string)
    iso_duration = times.FormatDuration(duration)
    return re.sub('[-PT]', '', iso_duration).lower()

  def GetFleetClusterUpgradeInfo(self, fleet, feature, args):
    """Gets Cluster Upgrade Feature information for the provided Fleet."""
    if (
        args.IsKnownAndSpecified('show_linked_cluster_upgrade')
        and args.show_linked_cluster_upgrade
    ):
      return self.GetLinkedClusterUpgrades(fleet, feature)
    return Describe.GetClusterUpgradeInfo(fleet, feature)

  @staticmethod
  def GetClusterUpgradeInfo(fleet, feature):
    """Gets Cluster Upgrade Feature information for the provided Fleet."""
    fleet_spec = feature.spec.clusterupgrade
    if not fleet_spec:
      msg = ('Cluster Upgrade feature is not configured for Fleet: {}.').format(
          fleet
      )
      raise exceptions.Error(msg)

    res = {
        'fleet': fleet,
        'spec': Describe.FormatDurations(fleet_spec),
    }
    if feature.state is not None and feature.state.clusterupgrade is not None:
      res['state'] = feature.state.clusterupgrade
    return res

  def GetLinkedClusterUpgrades(self, fleet, feature):
    """Gets Cluster Upgrade Feature information for the entire sequence."""

    current_project = Describe.GetProjectIDFromFleet(fleet)
    visited = set([fleet])

    def _UpTheStream(cluster_upgrade):
      """Recursively gets information for the upstream Fleets."""
      upstream_spec = cluster_upgrade.get('spec', None)
      upstream_fleets = upstream_spec.upstreamFleets if upstream_spec else None
      if not upstream_fleets:
        return [cluster_upgrade]

      # Currently, we only process the first upstream Fleet in the
      # Cluster Upgrade Feature, forming a linked-list of Fleets. If the API
      # ever supports multiple upstream Fleets (i.e., graph of Fleets), this
      # will need to be modified to recurse on every Fleet.
      upstream_fleet = upstream_fleets[0]
      if upstream_fleet in visited:
        return [cluster_upgrade]  # Detected a cycle.
      visited.add(upstream_fleet)

      upstream_fleet_project = Describe.GetProjectIDFromFleet(upstream_fleet)
      upstream_feature = (
          feature
          if upstream_fleet_project == current_project
          else self.GetFeature(project=upstream_fleet_project)
      )
      try:
        upstream_cluster_upgrade = Describe.GetClusterUpgradeInfo(
            upstream_fleet, upstream_feature
        )
      except exceptions.Error as e:
        log.warning(e)
        return [cluster_upgrade]
      return _UpTheStream(upstream_cluster_upgrade) + [cluster_upgrade]

    def _DownTheStream(cluster_upgrade):
      """Recursively gets information for the downstream Fleets."""
      downstream_state = cluster_upgrade.get('state', None)
      downstream_fleets = (
          downstream_state.downstreamFleets if downstream_state else None
      )
      if not downstream_fleets:
        return [cluster_upgrade]

      # Currently, we only process the first downstream Fleet in the
      # Cluster Upgrade Feature, forming a linked-list of Fleet. If the API
      # ever supports multiple downstream Fleets (i.e., graph of Fleets), this
      # will need to be modified to recurse on every Scope.
      downstream_fleet = downstream_fleets[0]
      if downstream_fleet in visited:
        return [cluster_upgrade]  # Detected a cycle.
      visited.add(downstream_fleet)

      downstream_scope_project = Describe.GetProjectIDFromFleet(
          downstream_fleet
      )
      downstream_feature = (
          feature
          if downstream_scope_project == current_project
          else self.GetFeature(project=downstream_scope_project)
      )
      downstream_cluster_upgrade = Describe.GetClusterUpgradeInfo(
          downstream_fleet, downstream_feature
      )
      return [cluster_upgrade] + _DownTheStream(downstream_cluster_upgrade)

    current_cluster_upgrade = Describe.GetClusterUpgradeInfo(fleet, feature)
    upstream_cluster_upgrades = _UpTheStream(current_cluster_upgrade)[:-1]
    downstream_cluster_upgrades = _DownTheStream(current_cluster_upgrade)[1:]
    return (
        upstream_cluster_upgrades
        + [current_cluster_upgrade]
        + downstream_cluster_upgrades
    )
