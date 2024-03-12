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
"""Helpers for the container cluster related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.container import admin_users
from googlecloudsdk.command_lib.edge_cloud.container import fleet
from googlecloudsdk.command_lib.edge_cloud.container import resource_args
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import resources


def GetClusterCreateRequest(args, release_track):
  """Get cluster create request message.

  Args:
    args: comand line arguments.
    release_track: release track of the command.

  Returns:
    message obj, cluster create request message.
  """
  messages = util.GetMessagesModule(release_track)
  cluster_ref = GetClusterReference(args)
  req = messages.EdgecontainerProjectsLocationsClustersCreateRequest(
      cluster=messages.Cluster(),
      clusterId=cluster_ref.clustersId,
      parent=cluster_ref.Parent().RelativeName(),
  )
  PopulateClusterMessage(req, messages, args)
  if release_track == base.ReleaseTrack.ALPHA:
    PopulateClusterAlphaMessage(req, messages, args)
  return req


def GetClusterUpgradeRequest(args, release_track):
  """Get cluster upgrade request message.

  Args:
    args: comand line arguments.
    release_track: release track of the command.

  Returns:
    message obj, cluster upgrade request message.
  """
  messages = util.GetMessagesModule(release_track)
  cluster_ref = GetClusterReference(args)
  upgrade_cluster_req = messages.UpgradeClusterRequest()
  upgrade_cluster_req.targetVersion = args.version
  if args.schedule.upper() != 'IMMEDIATELY':
    raise ValueError('Unsupported --schedule value: ' + args.schedule)
  upgrade_cluster_req.schedule = (
      messages.UpgradeClusterRequest.ScheduleValueValuesEnum(
          args.schedule.upper()
      )
  )
  req = messages.EdgecontainerProjectsLocationsClustersUpgradeRequest()
  req.name = cluster_ref.RelativeName()
  req.upgradeClusterRequest = upgrade_cluster_req
  return req


def PopulateClusterMessage(req, messages, args):
  """Fill the cluster message from command arguments.

  Args:
    req: create cluster request message.
    messages: message module of edgecontainer cluster.
    args: command line arguments.
  """
  # cluster service IPV4 CIDR blocks have default values.
  req.cluster.networking = messages.ClusterNetworking()
  req.cluster.networking.clusterIpv4CidrBlocks = [args.cluster_ipv4_cidr]
  req.cluster.networking.servicesIpv4CidrBlocks = [args.services_ipv4_cidr]
  if flags.FlagIsExplicitlySet(args, 'default_max_pods_per_node'):
    req.cluster.defaultMaxPodsPerNode = int(args.default_max_pods_per_node)
  if flags.FlagIsExplicitlySet(args, 'labels'):
    req.cluster.labels = messages.Cluster.LabelsValue()
    req.cluster.labels.additionalProperties = []
    for key, value in args.labels.items():
      v = messages.Cluster.LabelsValue.AdditionalProperty()
      v.key = key
      v.value = value
      req.cluster.labels.additionalProperties.append(v)
  if (
      flags.FlagIsExplicitlySet(args, 'maintenance_window_recurrence')
      or flags.FlagIsExplicitlySet(args, 'maintenance_window_start')
      or flags.FlagIsExplicitlySet(args, 'maintenance_window_end')
  ):
    req.cluster.maintenancePolicy = messages.MaintenancePolicy()
    req.cluster.maintenancePolicy.window = messages.MaintenanceWindow()
    req.cluster.maintenancePolicy.window.recurringWindow = (
        messages.RecurringTimeWindow()
    )
    if flags.FlagIsExplicitlySet(args, 'maintenance_window_recurrence'):
      req.cluster.maintenancePolicy.window.recurringWindow.recurrence = (
          args.maintenance_window_recurrence
      )
    req.cluster.maintenancePolicy.window.recurringWindow.window = (
        messages.TimeWindow()
    )
    if flags.FlagIsExplicitlySet(args, 'maintenance_window_start'):
      req.cluster.maintenancePolicy.window.recurringWindow.window.startTime = (
          args.maintenance_window_start
      )
    if flags.FlagIsExplicitlySet(args, 'maintenance_window_end'):
      req.cluster.maintenancePolicy.window.recurringWindow.window.endTime = (
          args.maintenance_window_end
      )
  if flags.FlagIsExplicitlySet(args, 'control_plane_kms_key'):
    req.cluster.controlPlaneEncryption = messages.ControlPlaneEncryption()
    req.cluster.controlPlaneEncryption.kmsKey = args.control_plane_kms_key
  admin_users.SetAdminUsers(messages, args, req)
  fleet.SetFleetProjectPath(GetClusterReference(args), args, req)

  if flags.FlagIsExplicitlySet(args, 'external_lb_ipv4_address_pools'):
    req.cluster.externalLoadBalancerIpv4AddressPools = (
        args.external_lb_ipv4_address_pools
    )
  if flags.FlagIsExplicitlySet(args, 'version'):
    req.cluster.targetVersion = args.version
  if flags.FlagIsExplicitlySet(args, 'release_channel'):
    req.cluster.releaseChannel = messages.Cluster.ReleaseChannelValueValuesEnum(
        args.release_channel.upper()
    )
  if (
      flags.FlagIsExplicitlySet(args, 'control_plane_node_location')
      or flags.FlagIsExplicitlySet(args, 'control_plane_node_count')
      or flags.FlagIsExplicitlySet(args, 'control_plane_machine_filter')
  ):
    # creating an LCP cluster.
    req.cluster.controlPlane = messages.ControlPlane()
    req.cluster.controlPlane.local = messages.Local()
    if flags.FlagIsExplicitlySet(args, 'control_plane_node_location'):
      req.cluster.controlPlane.local.nodeLocation = (
          args.control_plane_node_location
      )
    if flags.FlagIsExplicitlySet(args, 'control_plane_node_count'):
      req.cluster.controlPlane.local.nodeCount = int(
          args.control_plane_node_count
      )
    if flags.FlagIsExplicitlySet(args, 'control_plane_machine_filter'):
      req.cluster.controlPlane.local.machineFilter = (
          args.control_plane_machine_filter
      )
    if flags.FlagIsExplicitlySet(
        args, 'control_plane_shared_deployment_policy'
    ):
      req.cluster.controlPlane.local.sharedDeploymentPolicy = (
          messages.Local.SharedDeploymentPolicyValueValuesEnum(
              args.control_plane_shared_deployment_policy.upper()
          )
      )


def PopulateClusterAlphaMessage(req, messages, args):
  """Filled the Alpha cluster message from command arguments.

  Args:
    req: create cluster request message.
    messages: message module of edgecontainer cluster.
    args: command line arguments.
  """
  if flags.FlagIsExplicitlySet(args, 'cluster_ipv6_cidr'):
    req.cluster.networking.clusterIpv6CidrBlocks = [args.cluster_ipv6_cidr]
  if flags.FlagIsExplicitlySet(args, 'services_ipv6_cidr'):
    req.cluster.networking.servicesIpv6CidrBlocks = [args.services_ipv6_cidr]
  if flags.FlagIsExplicitlySet(args, 'external_lb_ipv6_address_pools'):
    req.cluster.externalLoadBalancerIpv6AddressPools = (
        args.external_lb_ipv6_address_pools
    )
  resource_args.SetSystemAddonsConfig(args, req)
  if flags.FlagIsExplicitlySet(args, 'offline_reboot_ttl'):
    req.cluster.survivabilityConfig = messages.SurvivabilityConfig()
    req.cluster.survivabilityConfig.offlineRebootTtl = (
        json.dumps(args.offline_reboot_ttl) + 's'
    )


def IsLCPCluster(args):
  """Identify if the command is creating LCP cluster.

  Args:
    args: command line arguments.

  Returns:
    Boolean, indication of LCP cluster.
  """
  if (
      flags.FlagIsExplicitlySet(args, 'control_plane_node_location')
      and flags.FlagIsExplicitlySet(args, 'control_plane_node_count')
      and flags.FlagIsExplicitlySet(args, 'external_lb_ipv4_address_pools')
  ):
    return True
  return False


def IsOfflineCredential(args):
  """Identify if the command is requesting an offline credential for LCP cluster.

  Args:
    args: command line arguments.

  Returns:
    Boolean, indication of requesting offline credential.
  """
  if flags.FlagIsExplicitlySet(args, 'offline_credential'):
    return True
  return False


def GetClusterReference(args):
  """Get edgecontainer cluster resources.

  Args:
    args: command line arguments.

  Returns:
    edgecontainer cluster resources.
  """
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.cluster.Parse().RelativeName(),
      collection='edgecontainer.projects.locations.clusters',
  )


def ValidateClusterCreateRequest(req, release_track):
  """Validate cluster create request message.

  Args:
    req: Create cluster request message.
    release_track: Release track of the command.

  Returns:
    Single string of error message.
  """
  messages = util.GetMessagesModule(release_track)
  if (
      req.cluster.releaseChannel
      == messages.Cluster.ReleaseChannelValueValuesEnum.REGULAR
      and req.cluster.targetVersion is not None
  ):
    return (
        'Invalid Argument: REGULAR release channel does not support'
        ' specification of version'
    )
  return None
