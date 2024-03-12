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
"""Command for creating Workstation configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workstations import configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workstations import flags as workstations_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  """Create a workstation configuration.

  Create a workstation configuration.

  ## EXAMPLES

    To create a configuration with the 'e2-standard-8' machine type and a
    IntelliJ image, run:

      $ {command} CONFIG --machine-type=e2-standard-8
        --container-predefined-image=intellij

    To create a configuration with a Shielded VM instance that enables Secure
    Boot, virtual trusted platform module (vTPM) and integrity monitoring, run:

      $ {command} CONFIG --machine-type=e2-standard-4 --shielded-secure-boot
        --shielded-vtpm --shielded-integrity-monitoring

    To create a configuration with a non-default persistent disk containing 10GB
    of PD SSD storage, run:
      $ {command} CONFIG --machine-type=e2-standard-4 --pd-disk-type=pd-ssd
        --pd-disk-size=10
  """

  @classmethod
  def Args(cls, parser):
    workstations_flags.AddAsyncFlag(parser)
    workstations_flags.AddConfigResourceArg(parser)
    workstations_flags.AddIdleTimeoutFlag(parser)
    workstations_flags.AddRunningTimeoutFlag(parser)
    workstations_flags.AddMachineTypeFlag(parser)
    workstations_flags.AddServiceAccountFlag(parser)
    workstations_flags.AddServiceAccountScopes(parser)
    workstations_flags.AddNetworkTags(parser)
    workstations_flags.AddPoolSize(parser)
    workstations_flags.AddDisablePublicIpAddresses(parser)
    workstations_flags.AddDisableTcpConnections(parser)
    workstations_flags.AddShieldedSecureBoot(parser)
    workstations_flags.AddShieldedVtpm(parser)
    workstations_flags.AddShieldedIntegrityMonitoring(parser)
    workstations_flags.AddEnableAuditAgent(parser)
    workstations_flags.AddEnableConfidentialCompute(parser)
    workstations_flags.AddEnableNestedVirtualization(parser)
    workstations_flags.AddBootDiskSize(parser)
    workstations_flags.AddPdDiskType(parser)
    workstations_flags.AddPdDiskSize(parser)
    workstations_flags.AddPdReclaimPolicy(parser)
    workstations_flags.AddContainerImageField(parser)
    workstations_flags.AddContainerCommandField(parser)
    workstations_flags.AddContainerArgsField(parser)
    workstations_flags.AddContainerEnvField(parser)
    workstations_flags.AddContainerWorkingDirField(parser)
    workstations_flags.AddContainerRunAsUserField(parser)
    workstations_flags.AddEncryptionKeyFields(parser)
    workstations_flags.AddLabelsField(parser)
    workstations_flags.AddReplicaZones(parser)
    workstations_flags.AddEphemeralDirectory(parser)
    if (cls.ReleaseTrack() != base.ReleaseTrack.GA):
      workstations_flags.AddAcceleratorFields(parser)
      workstations_flags.AddDisableSSHToVM(parser)

  def Collection(self):
    return 'workstations.projects.locations.workstationClusters.workstationConfigs'

  def Run(self, args):
    client = configs.Configs(self.ReleaseTrack())
    response = client.Create(args)
    return response
