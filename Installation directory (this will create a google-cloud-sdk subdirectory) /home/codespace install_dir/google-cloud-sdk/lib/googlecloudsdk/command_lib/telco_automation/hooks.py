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
"""Declarative hooks for TelcoAutomation surface arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
import googlecloudsdk.generated_clients.apis.telcoautomation.v1.telcoautomation_v1_messages as GAConfig
import googlecloudsdk.generated_clients.apis.telcoautomation.v1alpha1.telcoautomation_v1alpha1_messages as AlphaConfig


def UpdateRequestWithInput(unused_ref, args, request):
  """Update request to add management config parameters."""
  fullmanagementconfig = args.full_management_config
  if fullmanagementconfig:
    fullmanagementconfigobject = GetVersionedFullMaanagementConfig(args)
    fullmanagementconfigobject.network = args.network
    fullmanagementconfigobject.subnet = args.subnet
    fullmanagementconfigobject.masterIpv4CidrBlock = args.master_ipv4_cidr_block
    fullmanagementconfigobject.clusterCidrBlock = args.cluster_cidr_block
    fullmanagementconfigobject.servicesCidrBlock = args.services_cidr_block
    fullmanagementconfigobject.clusterNamedRange = args.cluster_named_range
    fullmanagementconfigobject.servicesNamedRange = args.services_named_range
    fullmanagementconfigobject.masterAuthorizedNetworksConfig = (
        GetVersionedMasterAuthorizedNetworksConfig(args)
    )
    fullmanagementconfigobject.masterAuthorizedNetworksConfig.cidrBlocks = (
        args.cidr_blocks
    )
    request.orchestrationCluster.managementConfig.fullManagementConfig = (
        fullmanagementconfigobject
    )
    request.orchestrationCluster.managementConfig.standardManagementConfig = (
        None
    )
  return request


def GetVersionedFullMaanagementConfig(args):
  version = GetApiVersion(args)
  if version == 'v1alpha1':
    return AlphaConfig.FullManagementConfig()
  else:
    return GAConfig.FullManagementConfig()


def GetVersionedMasterAuthorizedNetworksConfig(args):
  version = GetApiVersion(args)
  if version == 'v1alpha1':
    return AlphaConfig.MasterAuthorizedNetworksConfig()
  else:
    return GAConfig.MasterAuthorizedNetworksConfig()


def GetApiVersion(args):
  if (
      hasattr(args, 'calliope_command')
      and args.calliope_command.ReleaseTrack() == calliope_base.ReleaseTrack.GA
  ):
    return 'v1'
  else:
    return 'v1alpha1'
