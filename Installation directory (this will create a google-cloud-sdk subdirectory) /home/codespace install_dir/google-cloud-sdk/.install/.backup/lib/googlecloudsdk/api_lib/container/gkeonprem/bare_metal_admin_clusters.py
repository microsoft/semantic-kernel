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
"""Utilities for gkeonprem API clients for bare metal admin cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class _BareMetalAdminClusterClient(client.ClientBase):
  """Base class for GKE OnPrem Bare Metal Admin Cluster API clients."""

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    annotations = getattr(args, 'annotations', {})
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          messages.BareMetalAdminCluster.AnnotationsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    return messages.BareMetalAdminCluster.AnnotationsValue(
        additionalProperties=additional_property_messages
    )

  def _island_mode_cidr_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminIslandModeCidrConfig."""
    kwargs = {
        'serviceAddressCidrBlocks': getattr(
            args, 'island_mode_service_address_cidr_blocks', []
        ),
        'podAddressCidrBlocks': getattr(
            args, 'island_mode_pod_address_cidr_blocks', []
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminIslandModeCidrConfig(**kwargs)

    return None

  def _network_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminNetworkConfig."""
    kwargs = {
        'islandModeCidr': self._island_mode_cidr_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminNetworkConfig(**kwargs)

    return None

  def _vip_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminVipConfig."""
    kwargs = {
        'controlPlaneVip': getattr(args, 'control_plane_vip', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminVipConfig(**kwargs)

    return None

  def _port_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminPortConfig."""
    kwargs = {
        'controlPlaneLoadBalancerPort': getattr(
            args, 'control_plane_load_balancer_port', None
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminPortConfig(**kwargs)

    return None

  def _manual_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminManualLbConfig."""
    kwargs = {
        'enabled': getattr(args, 'enable_manual_lb', False),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminManualLbConfig(**kwargs)

    return None

  def _load_balancer_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminLoadBalancerConfig."""
    kwargs = {
        'manualLbConfig': self._manual_lb_config(args),
        'portConfig': self._port_config(args),
        'vipConfig': self._vip_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminLoadBalancerConfig(**kwargs)

    return None

  def _lvp_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLvpConfig."""
    kwargs = {
        'path': getattr(args, 'lvp_share_path', None),
        'storageClass': getattr(args, 'lvp_share_storage_class', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalLvpConfig(**kwargs)

    return None

  def _lvp_share_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLvpShareConfig."""
    kwargs = {
        'lvpConfig': self._lvp_config(args),
        'sharedPathPvCount': getattr(args, 'lvp_share_path_pv_count', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalLvpShareConfig(**kwargs)

    return None

  def _lvp_node_mounts_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLvpConfig."""
    kwargs = {
        'path': getattr(args, 'lvp_node_mounts_config_path', None),
        'storageClass': getattr(
            args, 'lvp_node_mounts_config_storage_class', None
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalLvpConfig(**kwargs)

    return None

  def _storage_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminStorageConfig."""
    kwargs = {
        'lvpShareConfig': self._lvp_share_config(args),
        'lvpNodeMountsConfig': self._lvp_node_mounts_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminStorageConfig(**kwargs)

    return None

  def _node_labels(self, labels):
    """Constructs proto message LabelsValue."""
    additional_property_messages = []
    if not labels:
      return None

    for key, value in labels.items():
      additional_property_messages.append(
          messages.BareMetalNodeConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.BareMetalNodeConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _control_plane_node_config(self, control_plane_node_config):
    """Constructs proto message BareMetalNodeConfig."""
    node_ip = control_plane_node_config.get('nodeIP', '')
    if not node_ip:
      raise exceptions.BadArgumentException(
          '--control_plane_node_configs_from_file',
          'Missing field [nodeIP] in Control Plane Node configs file.',
      )

    kwargs = {
        'nodeIp': node_ip,
        'labels': self._node_labels(
            control_plane_node_config.get('labels', {})
        ),
    }

    return messages.BareMetalNodeConfig(**kwargs)

  def _control_plane_node_configs_from_file(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message field node_configs."""
    if not args.control_plane_node_configs_from_file:
      return []

    control_plane_node_configs = args.control_plane_node_configs_from_file.get(
        'nodeConfigs', []
    )

    if not control_plane_node_configs:
      raise exceptions.BadArgumentException(
          '--control_plane_node_configs_from_file',
          'Missing field [nodeConfigs] in Control Plane Node configs file.',
      )

    control_plane_node_configs_messages = []
    for control_plane_node_config in control_plane_node_configs:
      control_plane_node_configs_messages.append(
          self._control_plane_node_config(control_plane_node_config)
      )

    return control_plane_node_configs_messages

  def _control_plane_node_taints(self, args: parser_extensions.Namespace):
    """Constructs proto message NodeTaint."""
    taint_messages = []
    node_taints = getattr(args, 'control_plane_node_taints', {})
    if not node_taints:
      return []

    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))

    return taint_messages

  def _control_plane_node_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message LabelsValue."""
    node_labels = getattr(args, 'control_plane_node_labels', {})
    additional_property_messages = []
    if not node_labels:
      return None

    for key, value in node_labels.items():
      additional_property_messages.append(
          messages.BareMetalNodePoolConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.BareMetalNodePoolConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _parse_node_labels(self, node_labels):
    """Validates and parses a node label object.

    Args:
      node_labels: str of key-val pairs separated by ';' delimiter.

    Returns:
      If label is valid, returns a dict mapping message LabelsValue to its
      value, otherwise, raise ArgumentTypeError.
      For example,
      {
          'key': LABEL_KEY
          'value': LABEL_VALUE
      }
    """
    if not node_labels.get('labels'):
      return None

    input_node_labels = node_labels.get('labels', '').split(';')
    additional_property_messages = []

    for label in input_node_labels:
      key_val_pair = label.split('=')
      if len(key_val_pair) != 2:
        raise arg_parsers.ArgumentTypeError(
            'Node Label [{}] not in correct format, expect KEY=VALUE.'.format(
                input_node_labels
            )
        )
      additional_property_messages.append(
          messages.BareMetalNodeConfig.LabelsValue.AdditionalProperty(
              key=key_val_pair[0], value=key_val_pair[1]
          )
      )

    labels_value_message = messages.BareMetalNodeConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _node_config(self, node_config_args):
    """Constructs proto message BareMetalNodeConfig."""
    kwargs = {
        'nodeIp': node_config_args.get('node-ip', ''),
        'labels': self._parse_node_labels(node_config_args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodeConfig(**kwargs)

    return None

  def _control_plane_node_configs_from_flag(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message field node_configs."""
    node_config_flag_value = (
        getattr(args, 'control_plane_node_configs', [])
        if args.control_plane_node_configs
        else []
    )

    return [
        self._node_config(node_config) for node_config in node_config_flag_value
    ]

  def _node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalNodePoolConfig."""
    if 'control_plane_node_configs_from_file' in args.GetSpecifiedArgsDict():
      node_configs = self._control_plane_node_configs_from_file(args)
    else:
      node_configs = self._control_plane_node_configs_from_flag(args)

    kwargs = {
        'nodeConfigs': node_configs,
        'labels': self._control_plane_node_labels(args),
        'taints': self._control_plane_node_taints(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)

    return None

  def _control_plane_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminControlPlaneNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminControlPlaneNodePoolConfig(**kwargs)

    return None

  def _api_server_args(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminApiServerArgument."""
    api_server_args = []
    api_server_args_flag_value = getattr(args, 'api_server_args', None)
    if api_server_args_flag_value:
      for key, val in api_server_args_flag_value.items():
        api_server_args.append(
            messages.BareMetalAdminApiServerArgument(argument=key, value=val)
        )

    return api_server_args

  def _control_plane_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminControlPlaneConfig."""
    kwargs = {
        'controlPlaneNodePoolConfig': self._control_plane_node_pool_config(
            args
        ),
        'apiServerArgs': self._api_server_args(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminControlPlaneConfig(**kwargs)

    return None

  def _proxy_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminProxyConfig."""
    kwargs = {
        'uri': getattr(args, 'uri', None),
        'noProxy': getattr(args, 'no_proxy', []),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminProxyConfig(**kwargs)

    return None

  def _cluster_operations_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminClusterOperationsConfig ."""
    kwargs = {
        'enableApplicationLogs': getattr(args, 'enable_application_logs', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminClusterOperationsConfig(**kwargs)

    return None

  def _maintenance_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminMaintenanceConfig."""
    kwargs = {
        'maintenanceAddressCidrBlocks': getattr(
            args, 'maintenance_address_cidr_blocks', []
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminMaintenanceConfig(**kwargs)

    return None

  def _workload_node_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminWorkloadNodeConfig."""
    kwargs = {
        'maxPodsPerNode': getattr(args, 'max_pods_per_node', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminWorkloadNodeConfig(**kwargs)

    return None

  def _node_access_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminNodeAccessConfig."""
    kwargs = {
        'loginUser': getattr(args, 'login_user', 'root'),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminNodeAccessConfig(**kwargs)

    return None

  # TODO(b/257292798): Move to common directory
  def _cluster_users(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message ClusterUser."""
    cluster_user_messages = []
    admin_users = getattr(args, 'admin_users', None)
    if admin_users:
      return [
          messages.ClusterUser(username=admin_user)
          for admin_user in admin_users
      ]

    # On create, client side default admin user to the current gcloud user.
    gcloud_config_core_account = properties.VALUES.core.account.Get()
    if gcloud_config_core_account:
      default_admin_user_message = messages.ClusterUser(
          username=gcloud_config_core_account
      )
      cluster_user_messages.append(default_admin_user_message)
      return cluster_user_messages

    return None

  def _authorization(self, args: parser_extensions.Namespace):
    """Constructs proto message Authorization."""
    kwargs = {
        'adminUsers': self._cluster_users(args),
    }

    if any(kwargs.values()):
      return messages.Authorization(**kwargs)

    return None

  def _security_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminSecurityConfig."""
    kwargs = {
        'authorization': self._authorization(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminSecurityConfig(**kwargs)

    return None

  def _bare_metal_admin_cluster(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalAdminCluster."""
    kwargs = {
        'name': self._admin_cluster_name(args),
        'description': getattr(args, 'description', None),
        'annotations': self._annotations(args),
        'bareMetalVersion': getattr(args, 'version', None),
        'networkConfig': self._network_config(args),
        'controlPlane': self._control_plane_config(args),
        'loadBalancer': self._load_balancer_config(args),
        'storage': self._storage_config(args),
        'proxy': self._proxy_config(args),
        'clusterOperations': self._cluster_operations_config(args),
        'maintenanceConfig': self._maintenance_config(args),
        'nodeConfig': self._workload_node_config(args),
        'nodeAccessConfig': self._node_access_config(args),
        'securityConfig': self._security_config(args),
        'binaryAuthorization': self._binary_authorization(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalAdminCluster(**kwargs)

    return None


class AdminClustersClient(_BareMetalAdminClusterClient):
  """Client for admin clusters in gkeonprem bare metal API."""

  def __init__(self, **kwargs):
    super(AdminClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_bareMetalAdminClusters

  def Enroll(self, args: parser_extensions.Namespace):
    """Enrolls an admin cluster to Anthos on bare metal."""
    kwargs = {
        'membership': self._admin_cluster_membership_name(args),
        'bareMetalAdminClusterId': self._admin_cluster_id(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalAdminClustersEnrollRequest(
        parent=self._admin_cluster_parent(args),
        enrollBareMetalAdminClusterRequest=messages.EnrollBareMetalAdminClusterRequest(
            **kwargs
        ),
    )
    return self._service.Enroll(req)

  def Unenroll(self, args: parser_extensions.Namespace):
    """Unenrolls an Anthos on bare metal admin cluster."""
    kwargs = {
        'name': self._admin_cluster_name(args),
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'ignoreErrors': self.GetFlag(args, 'ignore_errors'),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalAdminClustersUnenrollRequest(
        **kwargs
    )
    return self._service.Unenroll(req)

  def List(self, args: parser_extensions.Namespace):
    """Lists admin clusters in the GKE On-Prem bare metal API."""
    # Workaround for P4SA: Call query version config first, ignore the result.
    # Context: b/296435390#comment2
    project = (
        args.project if args.project else properties.VALUES.core.project.Get()
    )
    # Hard code location to `us-west1`, because it cannot handle `--location=-`.
    parent = 'projects/{project}/locations/{location}'.format(
        project=project, location='us-west1'
    )
    dummy_request = messages.GkeonpremProjectsLocationsBareMetalAdminClustersQueryVersionConfigRequest(
        parent=parent,
    )
    _ = self._service.QueryVersionConfig(dummy_request)

    # If location is not specified, and container_bare_metal/location is not set
    # list clusters of all locations within a project.
    if (
        'location' not in args.GetSpecifiedArgsDict()
        and not properties.VALUES.container_bare_metal.location.Get()
    ):
      args.location = '-'

    list_req = (
        messages.GkeonpremProjectsLocationsBareMetalAdminClustersListRequest(
            parent=self._location_name(args)
        )
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='bareMetalAdminClusters',
        batch_size=getattr(args, 'page_size', 100),
        limit=getattr(args, 'limit', None),
        batch_size_attribute='pageSize',
    )

  def QueryVersionConfig(self, args: parser_extensions.Namespace):
    """Query Anthos on bare metal admin version configuration."""
    kwargs = {
        'upgradeConfig_clusterName': self._admin_cluster_name(args),
        'parent': self._location_ref(args).RelativeName(),
    }

    # This is a workaround for the limitation in apitools with nested messages.
    encoding.AddCustomJsonFieldMapping(
        messages.GkeonpremProjectsLocationsBareMetalAdminClustersQueryVersionConfigRequest,
        'upgradeConfig_clusterName',
        'upgradeConfig.clusterName',
    )

    req = messages.GkeonpremProjectsLocationsBareMetalAdminClustersQueryVersionConfigRequest(
        **kwargs
    )
    return self._service.QueryVersionConfig(req)

  def Create(self, args: parser_extensions.Namespace):
    """Creates an admin cluster in Anthos on bare metal."""
    kwargs = {
        'parent': self._admin_cluster_parent(args),
        'validateOnly': getattr(args, 'validate_only', False),
        'bareMetalAdminCluster': self._bare_metal_admin_cluster(args),
        'bareMetalAdminClusterId': self._admin_cluster_id(args),
    }
    req = (
        messages.GkeonpremProjectsLocationsBareMetalAdminClustersCreateRequest(
            **kwargs
        )
    )
    return self._service.Create(req)

  def Update(self, args: parser_extensions.Namespace):
    """Updates an admin cluster in Anthos on bare metal."""
    kwargs = {
        'name': self._admin_cluster_name(args),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.BARE_METAL_ADMIN_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        'validateOnly': getattr(args, 'validate_only', False),
        'bareMetalAdminCluster': self._bare_metal_admin_cluster_for_update(
            args
        ),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalAdminClustersPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)

  def _bare_metal_admin_cluster_for_update(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message BareMetalAdminCluster."""
    kwargs = {
        'description': getattr(args, 'description', None),
        'bareMetalVersion': getattr(args, 'version', None),
        'networkConfig': self._network_config(args),
        'controlPlane': self._control_plane_config(args),
        'loadBalancer': self._load_balancer_config(args),
        'storage': self._storage_config(args),
        'proxy': self._proxy_config(args),
        'clusterOperations': self._cluster_operations_config(args),
        'maintenanceConfig': self._maintenance_config(args),
        'nodeConfig': self._workload_node_config(args),
        'nodeAccessConfig': self._node_access_config(args),
        'binaryAuthorization': self._binary_authorization(args),
    }
    if any(kwargs.values()):
      return messages.BareMetalAdminCluster(**kwargs)
    return None
