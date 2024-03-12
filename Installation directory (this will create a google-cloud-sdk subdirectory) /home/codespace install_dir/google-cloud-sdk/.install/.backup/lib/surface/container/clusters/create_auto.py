# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Create-auto cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags
from surface.container.clusters import create

# Select which flags are auto flags
auto_flags = [
    'args',
    'clusterversion',
    'masterauth',
    'nodeidentity',
    'privatecluster',
    'authenticatorsecurity',
    'databaseencryption',
    'bootdiskkms',
    'autoprovisioning_network_tags',
    'enableworkloadconfigaudit',
    'enableworkloadvulnscanning',
    'enableGoogleCloudAccess',
    'privateEndpointSubnetwork',
    'managedConfig',
    'fleetProject',
    'enableFleet',
    'enableSecurityPosture',
    'autoprovisioningEnableKubeletReadonlyPort',
    'dataplanev2obs',
    'enableK8sBetaApis',
    'securityPosture',
    'workloadVulnerabilityScanning',
    'enableRuntimeVulnerabilityInsight',
    'masterglobalaccess',
    'enableDnsEndpoint',
    'workloadPolicies',
    'containerdConfig',
    'labels',
    'secretManagerConfig',
    'enableCiliumClusterwideNetworkPolicy',
]

# Change default flag values in create-auto
flag_overrides = {
    'num_nodes': 1,
    'enable_ip_alias': True,
    'enable_master_authorized_networks': False,
    'privatecluster': {
        'private_cluster': None,
    },
}

auto_flag_defaults = dict(
    list(create.base_flag_defaults.items()) + list(flag_overrides.items())
)


def AddAutoFlags(parser, release_track):
  """Adds flags that are not same in create."""
  flags.AddLoggingFlag(parser, True)
  flags.AddMonitoringFlag(parser, True)
  flags.AddBinauthzFlags(parser, release_track=release_track, autopilot=True)
  flags.AddWorkloadPoliciesFlag(parser)
  flags.AddReleaseChannelFlag(parser, autopilot=True)
  flags.AddEnableBackupRestoreFlag(parser)
  flags.AddAutoprovisioningResourceManagerTagsCreate(parser)
  flags.AddAdditiveVPCScopeFlags(parser, release_track=release_track)
  flags.AddIPAliasRelatedFlags(parser, autopilot=True)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(create.Create):
  """Create an Autopilot cluster for running containers."""

  autopilot = True
  default_flag_values = auto_flag_defaults

  @staticmethod
  def Args(parser):
    create.AddFlags(create.GA, parser, auto_flag_defaults, auto_flags)
    AddAutoFlags(parser, base.ReleaseTrack.GA)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(create.CreateBeta):
  """Create an Autopilot cluster for running containers."""

  autopilot = True
  default_flag_values = auto_flag_defaults

  @staticmethod
  def Args(parser):
    create.AddFlags(create.BETA, parser, auto_flag_defaults, auto_flags)
    AddAutoFlags(parser, base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(create.CreateAlpha):
  """Create an Autopilot cluster for running containers."""

  autopilot = True
  default_flag_values = auto_flag_defaults

  @staticmethod
  def Args(parser):
    create.AddFlags(create.ALPHA, parser, auto_flag_defaults, auto_flags)
    AddAutoFlags(parser, base.ReleaseTrack.ALPHA)
