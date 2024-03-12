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

"""Command to create Cluster Ugprade Feature information for a Fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.clusterupgrade import flags as clusterupgrade_flags
from surface.container.fleet.clusterupgrade import update as clusterupgrade_update


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(clusterupgrade_update.Update):
  """Create the clusterupgrade feature for a fleet within a given project."""

  detailed_help = {"EXAMPLES": """\
            To create the clusterupgrade feature for the current fleet, run:

            $ {command} --default-upgrade-soaking=DEFAULT_UPGRADE_SOAKING
        """}

  @staticmethod
  def Args(parser):
    flags = clusterupgrade_flags.ClusterUpgradeFlags(parser)
    flags.AddDefaultUpgradeSoakingFlag()
    flags.AddUpgradeSoakingOverrideFlags(with_destructive=False)
    flags.AddUpstreamFleetFlags(with_destructive=False)
