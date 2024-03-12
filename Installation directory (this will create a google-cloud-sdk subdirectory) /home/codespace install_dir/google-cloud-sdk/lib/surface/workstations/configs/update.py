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
"""Command for updating Workstation configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workstations import configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workstations import flags as workstations_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Update(base.UpdateCommand):
  """Updates a workstation configuration.

  Updates a workstation configuration.

  ## EXAMPLES

    To update a configuration with the 'e2-standard-8' machine type and a
    IntelliJ image, run:

      $ {command} CONFIG --machine-type=e2-standard-8
        --container-predefined-image=intellij

    To update a configuration to disable Secure Boot, virtual trusted platform
    module (vTPM) and integrity monitoring, run:

      $ {command} CONFIG --no-shielded-secure-boot --no-shielded-vtpm
      --no-shielded-integrity-monitoring
  """

  @classmethod
  def Args(cls, parser):
    workstations_flags.AddAsyncFlag(parser)
    workstations_flags.AddConfigResourceArg(parser)
    workstations_flags.AddIdleTimeoutFlag(parser, use_default=False)
    workstations_flags.AddRunningTimeoutFlag(parser, use_default=False)
    workstations_flags.AddMachineTypeFlag(parser, use_default=False)
    workstations_flags.AddServiceAccountFlag(parser)
    workstations_flags.AddNetworkTags(parser)
    workstations_flags.AddPoolSize(parser, use_default=False)
    workstations_flags.AddDisablePublicIpAddresses(parser, use_default=False)

    workstations_flags.AddEnableTcpConnections(parser)
    workstations_flags.AddServiceAccountScopes(parser)
    workstations_flags.AddShieldedSecureBoot(parser, use_default=False)
    workstations_flags.AddShieldedVtpm(parser, use_default=False)
    workstations_flags.AddShieldedIntegrityMonitoring(parser, use_default=False)
    workstations_flags.AddEnableAuditAgent(parser, use_default=False)
    workstations_flags.AddEnableConfidentialCompute(parser, use_default=False)
    workstations_flags.AddEnableNestedVirtualization(parser, use_default=False)
    workstations_flags.AddBootDiskSize(parser, use_default=False)
    workstations_flags.AddContainerImageField(parser, use_default=False)
    workstations_flags.AddContainerCommandField(parser)
    workstations_flags.AddContainerArgsField(parser)
    workstations_flags.AddContainerEnvField(parser)
    workstations_flags.AddContainerWorkingDirField(parser)
    workstations_flags.AddContainerRunAsUserField(parser)
    workstations_flags.AddLabelsField(parser)
    if (cls.ReleaseTrack() != base.ReleaseTrack.GA):
      workstations_flags.AddAcceleratorFields(parser)
      workstations_flags.AddEnableSSHToVM(parser)

  def Collection(self):
    return (
        'workstations.projects.locations.workstationClusters.workstationConfigs'
    )

  def Run(self, args):
    client = configs.Configs(self.ReleaseTrack())
    response = client.Update(args)
    return response
