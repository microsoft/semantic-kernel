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
"""Base class for Cluster Upgrade Feature CRUD operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import times
import six

CLUSTER_UPGRADE_FEATURE = 'clusterupgrade'


class ClusterUpgradeCommand(object):
  """Base class for Cluster Upgrade Feature commands."""

  def __init__(self, args):
    self.feature_name = CLUSTER_UPGRADE_FEATURE
    self.args = args

  @staticmethod
  def GetScopeNameWithProjectNumber(name):
    """Rebuilds scope name with project number instead of ID."""
    delimiter = '/'
    tokens = name.split(delimiter)
    if len(tokens) != 6 or tokens[0] != 'projects':
      raise exceptions.Error(
          '{} is not a valid Scope resource name'.format(name))
    project_id = tokens[1]
    project_number = project_util.GetProjectNumber(project_id)
    tokens[1] = six.text_type(project_number)
    return delimiter.join(tokens)

  def ReleaseTrack(self):
    """Required to initialize HubClient. See calliope base class."""
    return self.args.calliope_command.ReleaseTrack()

  def IsClusterUpgradeRequest(self):
    """Checks if any Cluster Upgrade Feature related arguments are present."""
    cluster_upgrade_flags = {
        'upstream_scope',
        'reset_upstream_scope',
        'show_cluster_upgrade',
        'show_linked_cluster_upgrade',
        'default_upgrade_soaking',
        'remove_upgrade_soaking_overrides',
        'add_upgrade_soaking_override',
        'upgrade_selector',
    }
    return any(has_value and flag in cluster_upgrade_flags
               for flag, has_value in self.args.__dict__.items())


class DescribeCommand(feature_base.FeatureCommand, ClusterUpgradeCommand):
  """Command for describing a Scope's Cluster Upgrade Feature."""

  @staticmethod
  def GetProjectFromScopeName(name):
    """Extracts the project name from the full Scope resource name."""
    return name.split('/')[1]

  @staticmethod
  def FormatDurations(cluster_upgrade_spec):
    """Formats display strings for all cluster upgrade duration fields."""
    if cluster_upgrade_spec.postConditions is not None:
      default_soaking = cluster_upgrade_spec.postConditions.soaking
      if default_soaking is not None:
        cluster_upgrade_spec.postConditions.soaking = DescribeCommand.DisplayDuration(
            default_soaking)
    for override in cluster_upgrade_spec.gkeUpgradeOverrides:
      if override.postConditions is not None:
        override_soaking = override.postConditions.soaking
        if override_soaking is not None:
          override.postConditions.soaking = DescribeCommand.DisplayDuration(
              override_soaking)
    return cluster_upgrade_spec

  @staticmethod
  def DisplayDuration(proto_duration_string):
    """Returns the display string for a duration value."""
    duration = times.ParseDuration(proto_duration_string)
    iso_duration = times.FormatDuration(duration)
    return re.sub('[-PT]', '', iso_duration).lower()

  def GetScopeWithClusterUpgradeInfo(self, scope, feature):
    """Adds Cluster Upgrade Feature information to describe Scope response."""
    scope_name = ClusterUpgradeCommand.GetScopeNameWithProjectNumber(scope.name)
    if (self.args.IsKnownAndSpecified('show_cluster_upgrade') and
        self.args.show_cluster_upgrade):
      return self.AddClusterUpgradeInfoToScope(scope, scope_name, feature)
    elif (self.args.IsKnownAndSpecified('show_linked_cluster_upgrade') and
          self.args.show_linked_cluster_upgrade):
      serialized_scope = resource_projector.MakeSerializable(scope)
      serialized_scope['clusterUpgrades'] = self.GetLinkedClusterUpgradeScopes(
          scope_name, feature)
      return serialized_scope
    return scope

  def AddClusterUpgradeInfoToScope(self, scope, scope_name, feature):
    serialized_scope = resource_projector.MakeSerializable(scope)
    serialized_scope['clusterUpgrade'] = self.GetClusterUpgradeInfoForScope(
        scope_name, feature)
    return serialized_scope

  def GetClusterUpgradeInfoForScope(self, scope_name, feature):
    """Gets Cluster Upgrade Feature information for the provided Scope."""
    scope_specs = self.hubclient.ToPyDict(feature.scopeSpecs)
    if (scope_name not in scope_specs or
        not scope_specs[scope_name].clusterupgrade):
      msg = ('Cluster Upgrade feature is not configured for Scope: {}.'
            ).format(scope_name)
      raise exceptions.Error(msg)
    state = (
        self.hubclient.ToPyDefaultDict(
            self.messages.ScopeFeatureState, feature.scopeStates
        )[scope_name].clusterupgrade
        or self.messages.ClusterUpgradeScopeState()
    )

    return {
        'scope': scope_name,
        'state': state,
        'spec': DescribeCommand.FormatDurations(
            scope_specs[scope_name].clusterupgrade
        ),
    }

  def GetLinkedClusterUpgradeScopes(self, scope_name, feature):
    """Gets Cluster Upgrade Feature information for the entire sequence."""

    current_project = DescribeCommand.GetProjectFromScopeName(scope_name)
    visited = set([scope_name])

    def UpTheStream(cluster_upgrade):
      """Recursively gets information for the upstream Scopes."""
      upstream_spec = cluster_upgrade.get('spec', None)
      upstream_scopes = upstream_spec.upstreamScopes if upstream_spec else None
      if not upstream_scopes:
        return [cluster_upgrade]

      # Currently, we only process the first upstream Scope in the
      # Cluster Upgrade Feature, forming a linked-list of Scopes. If the API
      # ever supports multiple upstream Scopes (i.e., graph of Scopes), this
      # will need to be modified to recurse on every Scope.
      upstream_scope_name = upstream_scopes[0]
      if upstream_scope_name in visited:
        return [cluster_upgrade]  # Detected a cycle.
      visited.add(upstream_scope_name)

      upstream_scope_project = DescribeCommand.GetProjectFromScopeName(
          upstream_scope_name)
      upstream_feature = (
          feature if upstream_scope_project == current_project else
          self.GetFeature(project=upstream_scope_project))
      try:
        upstream_cluster_upgrade = self.GetClusterUpgradeInfoForScope(
            upstream_scope_name, upstream_feature)
      except exceptions.Error as e:
        log.warning(e)
        return [cluster_upgrade]
      return UpTheStream(upstream_cluster_upgrade) + [cluster_upgrade]

    def DownTheStream(cluster_upgrade):
      """Recursively gets information for the downstream Scopes."""
      downstream_state = cluster_upgrade.get('state', None)
      downstream_scopes = (
          downstream_state.downstreamScopes if downstream_state else None)
      if not downstream_scopes:
        return [cluster_upgrade]

      # Currently, we only process the first downstream Scope in the
      # Cluster Upgrade Feature, forming a linked-list of Scopes. If the API
      # ever supports multiple downstream Scopes (i.e., graph of Scopes), this
      # will need to be modified to recurse on every Scope.
      downstream_scope_name = downstream_scopes[0]
      if downstream_scope_name in visited:
        return [cluster_upgrade]  # Detected a cycle.
      visited.add(downstream_scope_name)

      downstream_scope_project = DescribeCommand.GetProjectFromScopeName(
          downstream_scope_name)
      downstream_feature = (
          feature if downstream_scope_project == current_project else
          self.GetFeature(project=downstream_scope_project))
      downstream_cluster_upgrade = self.GetClusterUpgradeInfoForScope(
          downstream_scope_name, downstream_feature)
      return [cluster_upgrade] + DownTheStream(downstream_cluster_upgrade)

    current_cluster_upgrade = self.GetClusterUpgradeInfoForScope(
        scope_name, feature)
    upstream_cluster_upgrades = UpTheStream(current_cluster_upgrade)[:-1]
    downstream_cluster_upgrades = DownTheStream(current_cluster_upgrade)[1:]
    return (upstream_cluster_upgrades + [current_cluster_upgrade] +
            downstream_cluster_upgrades)


class EnableCommand(feature_base.EnableCommandMixin, ClusterUpgradeCommand):
  """Base class for enabling the Cluster Upgrade Feature."""

  def GetWithForceEnable(self):
    """Gets the project's Cluster Upgrade Feature, enabling if necessary."""
    try:
      # Get the feature without transforming HTTP errors.
      return self.hubclient.GetFeature(self.FeatureResourceName())
    except apitools_exceptions.HttpNotFoundError:
      # It is expected for self.GetFeature to raise an exception when the
      # feature is not enabled. If that is the case, we enable it on behalf
      # of the caller.
      self.Enable(self.messages.Feature())
      return self.GetFeature()


class UpdateCommand(feature_base.UpdateCommandMixin, ClusterUpgradeCommand):
  """Base class for updating the Cluster Upgrade Feature."""

  def Update(self, feature, scope_name):
    """Updates Cluster Upgrade Feature information."""
    scope_specs_map = self.hubclient.ToPyDefaultDict(
        self.messages.ScopeFeatureSpec, feature.scopeSpecs)
    cluster_upgrade_spec = (
        scope_specs_map[scope_name].clusterupgrade or
        self.messages.ClusterUpgradeScopeSpec())

    self.HandleUpstreamScopes(cluster_upgrade_spec)
    self.HandleDefaultSoakTime(cluster_upgrade_spec)
    self.HandleUpgradeSoakingOverrides(cluster_upgrade_spec)

    scope_specs_map[scope_name].clusterupgrade = cluster_upgrade_spec
    patch = self.messages.Feature(
        scopeSpecs=self.hubclient.ToScopeSpecs(
            {scope_name: scope_specs_map[scope_name]}))

    # Until the Feature API supports update masking for map values, this
    # presents a potential race condition; however, this is incredibly unlikely
    # to occur in most customer use cases.
    return super(UpdateCommand, self).Update(['scopeSpecs'], patch)

  def HandleUpstreamScopes(self, cluster_upgrade_spec):
    """Updates the Cluster Upgrade Feature's upstreamScopes field based on provided arguments.
    """
    if (self.args.IsKnownAndSpecified('reset_upstream_scope') and
        self.args.reset_upstream_scope):
      cluster_upgrade_spec.upstreamScopes = []
    elif (self.args.IsKnownAndSpecified('upstream_scope') and
          self.args.upstream_scope is not None):
      cluster_upgrade_spec.upstreamScopes = [self.args.upstream_scope]

  def HandleDefaultSoakTime(self, cluster_upgrade_spec):
    """Updates the Cluster Upgrade Feature's postConditions.soaking field."""
    if (not self.args.IsKnownAndSpecified('default_upgrade_soaking') or
        self.args.default_upgrade_soaking is None):
      return

    default_soaking = times.FormatDurationForJson(
        self.args.default_upgrade_soaking)
    post_conditions = (
        cluster_upgrade_spec.postConditions or
        self.messages.ClusterUpgradePostConditions())
    post_conditions.soaking = default_soaking
    cluster_upgrade_spec.postConditions = post_conditions

  def HandleUpgradeSoakingOverrides(self, cluster_upgrade_spec):
    """Updates the ClusterUpgrade Feature's gkeUpgradeOverrides field."""
    if (self.args.IsKnownAndSpecified('remove_upgrade_soaking_overrides') and
        self.args.remove_upgrade_soaking_overrides):
      cluster_upgrade_spec.gkeUpgradeOverrides = []
    elif (self.args.IsKnownAndSpecified('add_upgrade_soaking_override') and
          self.args.IsKnownAndSpecified('upgrade_selector') and
          self.args.add_upgrade_soaking_override is not None and
          self.args.upgrade_selector is not None):
      soaking = times.FormatDurationForJson(
          self.args.add_upgrade_soaking_override)
      existing_gke_upgrade_overrides = (
          cluster_upgrade_spec.gkeUpgradeOverrides or [])
      new_gke_upgrade_override = (
          self.messages.ClusterUpgradeGKEUpgradeOverride())
      new_gke_upgrade_override.postConditions = self.messages.ClusterUpgradePostConditions(
          soaking=soaking)

      upgrade_name = self.args.upgrade_selector['name']
      upgrade_version = self.args.upgrade_selector['version']
      new_gke_upgrade_override.upgrade = self.messages.ClusterUpgradeGKEUpgrade(
          name=upgrade_name, version=upgrade_version)
      new_gke_upgrade_overrides = (
          existing_gke_upgrade_overrides + [new_gke_upgrade_override])
      cluster_upgrade_spec.gkeUpgradeOverrides = new_gke_upgrade_overrides
