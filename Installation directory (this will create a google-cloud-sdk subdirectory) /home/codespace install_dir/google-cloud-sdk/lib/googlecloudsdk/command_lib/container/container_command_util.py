# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command util functions for gcloud container commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import text


class Error(exceptions.Error):
  """Class for errors raised by container commands."""


class NodePoolError(Error):
  """Error when a node pool name doesn't match a node pool in the cluster."""


def _NodePoolFromCluster(cluster, node_pool_name):
  """Helper function to get node pool from a cluster, given its name."""
  for node_pool in cluster.nodePools:
    if node_pool.name == node_pool_name:
      # Node pools always have unique names.
      return node_pool
  raise NodePoolError(
      'No node pool found matching the name [{}].'.format(node_pool_name))


def _MasterUpgradeMessage(name, server_conf, cluster, new_version):
  """Returns the prompt message during a master upgrade.

  Args:
    name: str, the name of the cluster being upgraded.
    server_conf: the server config object.
    cluster: the cluster object.
    new_version: str, the name of the new version, if given.

  Raises:
    NodePoolError: if the node pool name can't be found in the cluster.

  Returns:
    str, a message about which nodes in the cluster will be upgraded and
        to which version.
  """
  if cluster:
    version_message = 'version [{}]'.format(cluster.currentMasterVersion)
  else:
    version_message = 'its current version'

  if not new_version and server_conf:
    new_version = server_conf.defaultClusterVersion

  if new_version:
    new_version_message = 'version [{}]'.format(new_version)
  else:
    new_version_message = 'the default cluster version'

  return ('Master of cluster [{}] will be upgraded from {} to {}.'.format(
      name, version_message, new_version_message))


def _NodeUpgradeMessage(name, cluster, node_pool_name, new_version,
                        new_image_type, new_machine_type, new_disk_type,
                        new_disk_size):
  """Returns the prompt message during a node upgrade.

  Args:
    name: str, the name of the cluster being upgraded.
    cluster: the cluster object.
    node_pool_name: str, the name of the node pool if the upgrade is for a
      specific node pool.
    new_version: str, the name of the new version, if given.
    new_image_type: str, the name of the new image type, if given.
    new_machine_type: str, the name of the new machine type, if given.
    new_disk_type: str, the name of the new disk type, if given.
    new_disk_size: int, the size of the new disk, if given.

  Raises:
    NodePoolError: if the node pool name can't be found in the cluster.

  Returns:
    str, a message about which nodes in the cluster will be upgraded and
        to which version, image, or config, if applicable.
  """
  node_message = 'All nodes'
  current_version = None
  if node_pool_name:
    node_message = '{} in node pool [{}]'.format(node_message, node_pool_name)
    if cluster:
      current_version = _NodePoolFromCluster(cluster, node_pool_name).version
  elif cluster:
    node_message = '{} ({} {})'.format(
        node_message, cluster.currentNodeCount,
        text.Pluralize(cluster.currentNodeCount, 'node'))
    current_version = cluster.currentNodeVersion

  if current_version:
    version_message = 'version [{}]'.format(current_version)
  else:
    version_message = 'its current version'

  if not new_version and cluster:
    new_version = cluster.currentMasterVersion

  if new_version:
    new_version_message = 'version [{}]'.format(new_version)
  else:
    new_version_message = 'the master version'

  def _UpgradeMessage(field, current, new):
    from_current = 'from {}'.format(current) if current else ''
    return '{} of cluster [{}] {} will change {} to {}.'.format(
        node_message, name, field, from_current, new)

  if new_image_type:
    image_type = None
    if cluster and node_pool_name:
      image_type = _NodePoolFromCluster(cluster,
                                        node_pool_name).config.imageType
    if image_type:
      return ('{} of cluster [{}] image will change from {} to {}.'.format(
          node_message, name, image_type, new_image_type))
    else:
      return ('{} of cluster [{}] image will change to {}.'.format(
          node_message, name, new_image_type))

  node_upgrade_messages = []
  if new_machine_type:
    machine_type = None
    if cluster and node_pool_name:
      machine_type = _NodePoolFromCluster(cluster,
                                          node_pool_name).config.machineType
    node_upgrade_messages.append(
        _UpgradeMessage('machine_type', machine_type, new_machine_type))

  if new_disk_type:
    disk_type = None
    if cluster and node_pool_name:
      disk_type = _NodePoolFromCluster(cluster,
                                       node_pool_name).config.diskType
    node_upgrade_messages.append(
        _UpgradeMessage('disk_type', disk_type, new_disk_type))

  if new_disk_size:
    disk_size = None
    if cluster and node_pool_name:
      disk_size = _NodePoolFromCluster(cluster,
                                       node_pool_name).config.diskSizeGb
    node_upgrade_messages.append(
        _UpgradeMessage('disk_size', disk_size, new_disk_size))

  if not node_upgrade_messages:
    return '{} of cluster [{}] will be upgraded from {} to {}.'.format(
        node_message, name, version_message, new_version_message)
  return ''.join(node_upgrade_messages)


def ClusterUpgradeMessage(name,
                          server_conf=None,
                          cluster=None,
                          master=False,
                          node_pool_name=None,
                          new_version=None,
                          new_image_type=None,
                          new_machine_type=None,
                          new_disk_type=None,
                          new_disk_size=None):
  """Get a message to print during gcloud container clusters upgrade.

  Args:
    name: str, the name of the cluster being upgraded.
    server_conf: the server config object.
    cluster: the cluster object.
    master: bool, if the upgrade applies to the master version.
    node_pool_name: str, the name of the node pool if the upgrade is for a
      specific node pool.
    new_version: str, the name of the new version, if given.
    new_image_type: str, the name of the new node image type, if given.
    new_machine_type: str, the name of the new machine type, if given.
    new_disk_type: str, the name of the new boot disk type, if given.
    new_disk_size: int, the size of the new boot disk in GB, if given.

  Raises:
    NodePoolError: if the node pool name can't be found in the cluster.

  Returns:
    str, a message about which nodes in the cluster will be upgraded and
        to which version.
  """
  if master:
    upgrade_message = _MasterUpgradeMessage(
        name, server_conf, cluster, new_version
    )
  else:
    upgrade_message = _NodeUpgradeMessage(
        name,
        cluster,
        node_pool_name,
        new_version,
        new_image_type,
        new_machine_type,
        new_disk_type,
        new_disk_size,
    )

  return (
      '{} This operation is long-running and will block other operations '
      'on the cluster (including delete) until it has run to completion.'
      .format(upgrade_message)
  )


def GetZoneOrRegion(args,
                    ignore_property=False,
                    required=True,
                    is_autopilot=False):
  """Get a location (zone or region) from argument or property.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    ignore_property: bool, if true, will get location only from argument.
    required: bool, if true, lack of zone will cause raise an exception.
    is_autopilot: bool, if true, region property will take precedence over zone.

  Raises:
    MinimumArgumentException: if location if required and not provided.

  Returns:
    str, a location selected by user.
  """
  location = getattr(args, 'location', None)
  zone = getattr(args, 'zone', None)
  region = getattr(args, 'region', None)

  if ignore_property:
    location_property = None
  elif is_autopilot and properties.VALUES.compute.region.Get():
    # region property if set takes precedence over zone when using autopilot.
    location_property = properties.VALUES.compute.region.Get()
  elif properties.VALUES.compute.zone.Get():
    # zone property if set takes precedence over region.
    location_property = properties.VALUES.compute.zone.Get()
  else:
    location_property = properties.VALUES.compute.region.Get()

  location = location or region or zone or location_property
  if required and not location:
    raise calliope_exceptions.MinimumArgumentException(
        ['--location', '--zone', '--region']
    )

  return location


def GetAutoUpgrade(args):
  """Gets the value of node auto-upgrade."""
  if args.IsSpecified('enable_autoupgrade'):
    return args.enable_autoupgrade
  if getattr(args, 'enable_kubernetes_alpha', False):
    return None
  # Return default value
  return args.enable_autoupgrade


def GetAutoRepair(args):
  """Gets the value of node auto-repair."""
  if args.IsSpecified('enable_autorepair'):
    return args.enable_autorepair
  # Some other flags force this. If the image type isn't compatible, they'll get
  # the most friendly error message this way.
  if getattr(args, 'release_channel', None):
    return True
  if getattr(args, 'enable_kubernetes_alpha', False):
    return None
  # Node pools using COS and UBUNTU support auto repairs, enable it for them by
  # default.
  return (args.image_type or '').lower() in [
      '', 'cos', 'cos_containerd', 'gci', 'ubuntu', 'ubuntu_containerd'
  ]


def ParseUpdateOptionsBase(args, locations):
  """Helper function to build ClusterUpdateOptions object from args.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    locations: list of strings. Zones in which cluster has nodes.

  Returns:
    ClusterUpdateOptions, object with data used to update cluster.
  """
  opts = api_adapter.UpdateClusterOptions(
      monitoring_service=args.monitoring_service,
      logging_service=args.logging_service,
      monitoring=args.monitoring,
      logging=args.logging,
      enable_stackdriver_kubernetes=args.enable_stackdriver_kubernetes,
      disable_addons=args.disable_addons,
      enable_autoscaling=args.enable_autoscaling,
      min_nodes=args.min_nodes,
      max_nodes=args.max_nodes,
      total_min_nodes=args.total_min_nodes,
      total_max_nodes=args.total_max_nodes,
      location_policy=args.location_policy,
      node_pool=args.node_pool,
      locations=locations,
      enable_master_authorized_networks=args.enable_master_authorized_networks,
      master_authorized_networks=args.master_authorized_networks,
      private_ipv6_google_access_type=args.private_ipv6_google_access_type,
      workload_pool=args.workload_pool,
      disable_workload_identity=args.disable_workload_identity,
      database_encryption_key=args.database_encryption_key,
      disable_database_encryption=args.disable_database_encryption,
      enable_vertical_pod_autoscaling=args.enable_vertical_pod_autoscaling,
      enable_autoprovisioning=args.enable_autoprovisioning,
      enable_mesh_certificates=args.enable_mesh_certificates,
      autoprovisioning_config_file=args.autoprovisioning_config_file,
      autoprovisioning_service_account=args.autoprovisioning_service_account,
      autoprovisioning_scopes=args.autoprovisioning_scopes,
      autoprovisioning_locations=args.autoprovisioning_locations,
      autoprovisioning_max_surge_upgrade=getattr(
          args, 'autoprovisioning_max_surge_upgrade', None),
      autoprovisioning_max_unavailable_upgrade=getattr(
          args, 'autoprovisioning_max_unavailable_upgrade', None),
      enable_autoprovisioning_surge_upgrade=getattr(
          args, 'enable_autoprovisioning_surge_upgrade', None),
      enable_autoprovisioning_blue_green_upgrade=getattr(
          args, 'enable_autoprovisioning_blue_green_upgrade', None),
      autoprovisioning_standard_rollout_policy=getattr(
          args, 'autoprovisioning_standard_rollout_policy', None),
      autoprovisioning_node_pool_soak_duration=getattr(
          args, 'autoprovisioning_node_pool_soak_duration', None),
      enable_autoprovisioning_autorepair=getattr(
          args, 'enable_autoprovisioning_autorepair', None),
      enable_autoprovisioning_autoupgrade=getattr(
          args, 'enable_autoprovisioning_autoupgrade', None),
      autoprovisioning_min_cpu_platform=getattr(
          args, 'autoprovisioning_min_cpu_platform', None),
      autoprovisioning_image_type=getattr(args, 'autoprovisioning_image_type',
                                          None),
      min_cpu=args.min_cpu,
      max_cpu=args.max_cpu,
      min_memory=args.min_memory,
      max_memory=args.max_memory,
      min_accelerator=args.min_accelerator,
      max_accelerator=args.max_accelerator,
      logging_variant=args.logging_variant,
      in_transit_encryption=getattr(args, 'in_transit_encryption', None),
      autoprovisioning_resource_manager_tags=(
          args.autoprovisioning_resource_manager_tags),
      )

  if (args.disable_addons and
      api_adapter.GCEPDCSIDRIVER in args.disable_addons):
    pdcsi_disabled = args.disable_addons[api_adapter.GCEPDCSIDRIVER]
    if pdcsi_disabled:
      console_io.PromptContinue(
          message='If the GCE Persistent Disk CSI Driver is disabled, then any '
          'pods currently using PersistentVolumes owned by the driver '
          'will fail to terminate. Any new pods that try to use those '
          'PersistentVolumes will also fail to start.',
          cancel_on_no=True)

  if (args.disable_addons and
      api_adapter.GCPFILESTORECSIDRIVER in args.disable_addons):
    filestorecsi_disabled = args.disable_addons[
        api_adapter.GCPFILESTORECSIDRIVER]
    if filestorecsi_disabled:
      console_io.PromptContinue(
          message='If the GCP Filestore CSI Driver is disabled, then any '
          'pods currently using PersistentVolumes owned by the driver '
          'will fail to terminate. Any new pods that try to use those '
          'PersistentVolumes will also fail to start.',
          cancel_on_no=True)

  if (args.disable_addons and
      api_adapter.GCSFUSECSIDRIVER in args.disable_addons):
    gcsfusecsi_disabled = args.disable_addons[
        api_adapter.GCSFUSECSIDRIVER]
    if gcsfusecsi_disabled:
      console_io.PromptContinue(
          message='If the Cloud Storage Fuse CSI Driver is disabled, then any '
          'pods currently using PersistentVolumes owned by the driver '
          'will fail to terminate. Any new pods that try to use those '
          'PersistentVolumes will also fail to start.',
          cancel_on_no=True)

  if (args.disable_addons and
      api_adapter.STATEFULHA in args.disable_addons):
    statefulha_disabled = args.disable_addons[
        api_adapter.STATEFULHA]
    if statefulha_disabled:
      console_io.PromptContinue(
          message='If the StatefulHA Addon is disabled, then any applications '
          'currently protected will no longer be updated for high availability '
          'configuration.',
          cancel_on_no=True)

  if (args.disable_addons and
      api_adapter.PARALLELSTORECSIDRIVER in args.disable_addons):
    parallelstorecsi_disabled = args.disable_addons[
        api_adapter.PARALLELSTORECSIDRIVER]
    if parallelstorecsi_disabled:
      console_io.PromptContinue(
          message='If the Parallelstore CSI Driver is disabled, then any '
          'pods currently using PersistentVolumes owned by the driver '
          'will fail to terminate. Any new pods that try to use those '
          'PersistentVolumes will also fail to start.',
          cancel_on_no=True)

  return opts
