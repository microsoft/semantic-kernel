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

"""Command to update Cluster Ugprade Feature information for a Fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.clusterupgrade import flags as clusterupgrade_flags
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times


CLUSTER_UPGRADE_FEATURE = 'clusterupgrade'


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(feature_base.UpdateCommand):
  """Update the clusterupgrade feature for a fleet within a given project."""

  detailed_help = {'EXAMPLES': """\
            To update the clusterupgrade feature for the current fleet, run:

            $ {command} --default-upgrade-soaking=DEFAULT_UPGRADE_SOAKING
        """}

  feature_name = CLUSTER_UPGRADE_FEATURE

  @staticmethod
  def Args(parser):
    flags = clusterupgrade_flags.ClusterUpgradeFlags(parser)
    flags.AddDefaultUpgradeSoakingFlag()
    flags.AddUpgradeSoakingOverrideFlags(with_destructive=True)
    flags.AddUpstreamFleetFlags(with_destructive=True)

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    enable_cmd = _EnableCommand(args)
    feature = enable_cmd.GetWithForceEnable(project)
    self.Update(feature, args)

  def Update(self, feature, args):
    """Updates Cluster Upgrade Feature information for a fleet."""
    cluster_upgrade_spec = (
        feature.spec.clusterupgrade or self.messages.ClusterUpgradeFleetSpec()
    )
    Update._HandleUpstreamFleets(args, cluster_upgrade_spec)
    self._HandleDefaultSoakTime(args, cluster_upgrade_spec)
    self._HandleUpgradeSoakingOverrides(args, cluster_upgrade_spec)
    patch = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            clusterupgrade=cluster_upgrade_spec
        )
    )
    path = (
        'spec.clusterupgrade'
        if feature.spec.clusterupgrade is not None
        else 'spec'
    )
    return super(Update, self).Update([path], patch)

  @staticmethod
  def _HandleUpstreamFleets(args, cluster_upgrade_spec):
    """Updates the Cluster Upgrade Feature's upstreamFleets field."""
    if (
        args.IsKnownAndSpecified('reset_upstream_fleet')
        and args.reset_upstream_fleet
    ):
      cluster_upgrade_spec.upstreamFleets = []
    elif (
        args.IsKnownAndSpecified('upstream_fleet')
        and args.upstream_fleet is not None
    ):
      cluster_upgrade_spec.upstreamFleets = [args.upstream_fleet]

  def _HandleDefaultSoakTime(self, args, cluster_upgrade_spec):
    """Updates the Cluster Upgrade Feature's postConditions.soaking field."""
    if (
        not args.IsKnownAndSpecified('default_upgrade_soaking')
        or args.default_upgrade_soaking is None
    ):
      return

    default_soaking = times.FormatDurationForJson(
        iso_duration.Duration(seconds=args.default_upgrade_soaking)
    )
    post_conditions = (
        cluster_upgrade_spec.postConditions
        or self.messages.ClusterUpgradePostConditions()
    )
    post_conditions.soaking = default_soaking
    cluster_upgrade_spec.postConditions = post_conditions

  def _HandleUpgradeSoakingOverrides(self, args, cluster_upgrade_spec):
    """Updates the ClusterUpgrade Feature's gkeUpgradeOverrides field."""
    if (
        args.IsKnownAndSpecified('remove_upgrade_soaking_overrides')
        and args.remove_upgrade_soaking_overrides
    ):
      cluster_upgrade_spec.gkeUpgradeOverrides = []
    elif (
        args.IsKnownAndSpecified('add_upgrade_soaking_override')
        and args.IsKnownAndSpecified('upgrade_selector')
        and args.add_upgrade_soaking_override is not None
        and args.upgrade_selector is not None
    ):
      soaking = times.FormatDurationForJson(
          iso_duration.Duration(seconds=args.add_upgrade_soaking_override)
      )
      existing_gke_upgrade_overrides = (
          cluster_upgrade_spec.gkeUpgradeOverrides or []
      )
      new_gke_upgrade_override = (
          self.messages.ClusterUpgradeGKEUpgradeOverride()
      )
      new_gke_upgrade_override.postConditions = (
          self.messages.ClusterUpgradePostConditions(soaking=soaking)
      )

      upgrade_name = args.upgrade_selector['name']
      upgrade_version = args.upgrade_selector['version']
      new_gke_upgrade_override.upgrade = self.messages.ClusterUpgradeGKEUpgrade(
          name=upgrade_name, version=upgrade_version
      )
      new_gke_upgrade_overrides = existing_gke_upgrade_overrides + [
          new_gke_upgrade_override
      ]
      cluster_upgrade_spec.gkeUpgradeOverrides = new_gke_upgrade_overrides


class _EnableCommand(feature_base.EnableCommandMixin):
  """Base class for enabling the Cluster Upgrade Feature."""

  def __init__(self, args):
    self.feature_name = CLUSTER_UPGRADE_FEATURE
    self.args = args

  def ReleaseTrack(self):
    """Required to initialize HubClient. See calliope base class."""
    return self.args.calliope_command.ReleaseTrack()

  def GetWithForceEnable(self, project):
    """Gets the project's Cluster Upgrade Feature, enabling if necessary."""
    try:
      # Get the feature without transforming HTTP errors.
      return self.hubclient.GetFeature(
          self.FeatureResourceName(project=project)
      )
    except apitools_exceptions.HttpNotFoundError:
      # It is expected for self.GetFeature to raise an exception when the
      # feature is not enabled. If that is the case, we enable it on behalf of
      # the caller.
      self.Enable(self.messages.Feature())
      return self.GetFeature()
