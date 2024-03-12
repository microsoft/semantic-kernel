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
"""Functions to add flags in cluster upgrade commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import parser_arguments


class ClusterUpgradeFlags:
  """Add flags to the cluster upgrade command surface."""

  def __init__(self, parser: parser_arguments.ArgumentInterceptor):
    self._parser = parser

  @property
  def parser(self):  # pylint: disable=invalid-name
    return self._parser

  def AddShowLinkedClusterUpgrade(self):
    """Adds the --show-linked-cluster-upgrade flag."""
    self.parser.add_argument(
        '--show-linked-cluster-upgrade',
        action='store_true',
        default=None,
        help="""\
        Shows the cluster upgrade feature information for the current fleet as
        well as information for all other fleets linked in the same rollout
        sequence (provided that the caller has permission to view the upstream
        and downstream fleets). This displays cluster upgrade information for
        fleets in the current fleet's rollout sequence in order of furthest
        upstream to downstream.

        To view the cluster upgrade feature information for the rollout
        sequence containing the current fleet, run:

          $ {command} --show-linked-cluster-upgrade
        """,
    )

  def AddDefaultUpgradeSoakingFlag(self):
    """Adds the --default-upgrade-soaking flag."""
    self.parser.add_argument(
        '--default-upgrade-soaking',
        type=arg_parsers.Duration(),
        help="""\
        Configures the default soaking duration for each upgrade propagating
        through the current fleet to become "COMPLETE". Soaking begins after
        all clusters in the fleet are on the target version, or after 30 days
        if all cluster upgrades are not complete. Once an upgrade state becomes
        "COMPLETE", it will automatically be propagated to the downstream
        fleet. Max is 30 days.

        To configure Rollout Sequencing for a fleet, this attribute must be
        set. To do this while specifying a default soaking duration of 7 days,
        run:

          $ {command} --default-upgrade-soaking=7d
        """,
    )

  def AddUpgradeSoakingOverrideFlags(self, with_destructive=False):
    if with_destructive:
      group = self.parser.add_mutually_exclusive_group()
      self._AddRemoveUpgradeSoakingOverridesFlag(group)
      self._AddUpgradeSoakingOverrideFlags(group)
    else:
      self._AddUpgradeSoakingOverrideFlags(self.parser)

  def _AddRemoveUpgradeSoakingOverridesFlag(
      self, group: parser_arguments.ArgumentInterceptor
  ):
    """Adds the --remove-upgrade-soaking-overrides flag.

    Args:
      group: The group that should contain the flag.
    """
    group.add_argument(
        '--remove-upgrade-soaking-overrides',
        action='store_true',
        default=None,
        help="""\
        Removes soaking time overrides for all upgrades propagating through the
        current fleet. Consequently, all upgrades will follow the soak time
        configured by `--default-upgrade-soaking` until new overrides are
        configured with `--add_upgrade_soaking_override` and
        `--upgrade_selector`.

        To remove all configured soaking time overrides, run:

          $ {command} --remove-upgrade-soaking-overrides
        """,
    )

  def _AddUpgradeSoakingOverrideFlags(
      self, group: parser_arguments.ArgumentInterceptor
  ):
    """Adds upgrade soaking override flags.

    Args:
      group: The group that should contain the upgrade soaking override flags.
    """
    group = group.add_group(help="""\
        Upgrade soaking override.

        Defines a specific soaking time override for a particular upgrade
        propagating through the current fleet that supercedes the default
        soaking duration configured by `--default-upgrade-soaking`.

        To set an upgrade soaking override of 12 hours for the upgrade with
        name, `k8s_control_plane`, and version, `1.23.1-gke.1000`, run:

          $ {command} \
              --add-upgrade-soaking-override=12h \
              --upgrade-selector=name="k8s_control_plane",version="1.23.1-gke.1000"
        """)
    self._AddAddUpgradeSoakingOverrideFlag(group)
    self._AddUpgradeSelectorFlag(group)

  def _AddAddUpgradeSoakingOverrideFlag(
      self, group: parser_arguments.ArgumentInterceptor
  ):
    """Adds the --add-upgrade-soaking-override flag.

    Args:
      group: The group that should contain the flag.
    """
    group.add_argument(
        '--add-upgrade-soaking-override',
        type=arg_parsers.Duration(),
        required=True,
        help="""\
        Overrides the soaking time for a particular upgrade name and version
        propagating through the current fleet. Set soaking to 0 days to bypass
        soaking and fast-forward the upgrade to the downstream fleet.

        See `$ gcloud topic datetimes` for information on duration formats.
        """,
    )

  def _AddUpgradeSelectorFlag(
      self, group: parser_arguments.ArgumentInterceptor
  ):
    """Adds the --ugprade-selector flag.

    Args:
      group: The group that should contain the flag.
    """
    # TODO(b/233397411): Add link to documentation here.
    group.add_argument(
        '--upgrade-selector',
        type=UpgradeSelector(),
        required=True,
        help="""\
        Name and version of the upgrade to be overridden where version is a
        full GKE version. Currently, name can be either `k8s_control_plane` or
        `k8s_node`.
        """,
    )

  def AddUpstreamFleetFlags(self, with_destructive=False):
    """Adds upstream fleet flags."""
    if with_destructive:
      group = self.parser.add_mutually_exclusive_group()
      self._AddUpstreamFleetFlag(group)
      self._AddResetUpstreamFleetFlag(group)
    else:
      self._AddUpstreamFleetFlag(self.parser)

  def _AddUpstreamFleetFlag(self, group: parser_arguments.ArgumentInterceptor):
    """Adds the --upstream-fleet flag.

    Args:
      group: The group that should contain the flag.
    """
    # TODO(b/233397411): Add link to documentation here.
    group.add_argument(
        '--upstream-fleet',
        type=str,
        help="""\
        The upstream fleet. GKE will finish upgrades on the upstream fleet
        before applying the same upgrades to the current fleet.

        To configure the upstream fleet, run:

        $ {command} \
            --upstream-fleet={upstream_fleet}
        """,
    )

  def _AddResetUpstreamFleetFlag(
      self, group: parser_arguments.ArgumentInterceptor
  ):
    """Adds the --reset-upstream-fleet flag.

    Args:
      group: The group that should contain the flag.
    """
    group.add_argument(
        '--reset-upstream-fleet',
        action='store_true',
        default=None,
        help="""\
        Clears the relationship between the current fleet and its upstream
        fleet in the rollout sequence.

        To remove the link between the current fleet and its upstream fleet,
        run:

          $ {command} --reset-upstream-fleet
        """,
    )


class UpgradeSelector(arg_parsers.ArgDict):
  """Extends the ArgDict type to properly parse --upgrade-selector argument."""

  def __init__(self):
    super(UpgradeSelector, self).__init__(
        spec={'name': str, 'version': str},
        required_keys=['name', 'version'],
        max_length=2,
    )
