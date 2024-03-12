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
"""Utilities for node pool resources in Anthos clusters on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters as clusters
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class _BareMetalNodePoolsClient(clusters.ClustersClient):
  """Base class for GKE OnPrem Bare Metal API clients."""

  def _node_taints(self, args: parser_extensions.Namespace):
    """Constructs proto message NodeTaint."""
    taint_messages = []
    node_taints = getattr(args, 'node_taints', {})
    if not node_taints:
      return []

    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))

    return taint_messages

  def _node_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message LabelsValue."""
    node_labels = getattr(args, 'node_labels', {})
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

  def _node_configs_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    if not args.node_configs_from_file:
      return []

    node_configs = args.node_configs_from_file.get('nodeConfigs', [])

    if not node_configs:
      raise exceptions.BadArgumentException(
          '--node_configs_from_file',
          'Missing field [nodeConfigs] in Node configs file.',
      )

    node_config_messages = []
    for node_config in node_configs:
      node_config_messages.append(self._bare_metal_node_config(node_config))

    return node_config_messages

  # TODO(b/260737834): Create a common function for all nodeConfigs
  def _bare_metal_node_config(self, node_config):
    """Constructs proto message BareMetalNodeConfig."""
    node_ip = node_config.get('nodeIP', '')
    if not node_ip:
      raise exceptions.BadArgumentException(
          '--node_configs_from_file',
          'Missing field [nodeIP] in Node configs file.',
      )

    kwargs = {
        'nodeIp': node_ip,
        'labels': self._node_config_labels(node_config.get('labels', {})),
    }

    return messages.BareMetalNodeConfig(**kwargs)

  def _node_config_labels(self, labels):
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

  def _node_configs_from_flag(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    node_configs = []
    node_config_flag_value = getattr(args, 'node_configs', None)
    if node_config_flag_value:
      for node_config in node_config_flag_value:
        node_configs.append(self.node_config(node_config))

    return node_configs

  def _serialized_image_pulls_disabled(self, args: parser_extensions.Namespace):
    if 'disable_serialize_image_pulls' in args.GetSpecifiedArgsDict():
      return True
    elif 'enable_serialize_image_pulls' in args.GetSpecifiedArgsDict():
      return False
    else:
      return None

  def _kubelet_config(self, args: parser_extensions.Namespace):
    kwargs = {
        'registryPullQps': self.GetFlag(args, 'registry_pull_qps'),
        'registryBurst': self.GetFlag(args, 'registry_burst'),
        'serializeImagePullsDisabled': self._serialized_image_pulls_disabled(
            args
        ),
    }
    if any(kwargs.values()):
      return messages.BareMetalKubeletConfig(**kwargs)
    return None

  def _node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalNodePoolConfig."""
    if 'node_configs_from_file' in args.GetSpecifiedArgsDict():
      node_configs = self._node_configs_from_file(args)
    else:
      node_configs = self._node_configs_from_flag(args)
    kwargs = {
        'nodeConfigs': node_configs,
        'labels': self._node_labels(args),
        'taints': self._node_taints(args),
        'kubeletConfig': self._kubelet_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)

    return None

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    annotations = getattr(args, 'annotations', {})
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          messages.BareMetalNodePool.AnnotationsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    annotation_value_message = messages.BareMetalNodePool.AnnotationsValue(
        additionalProperties=additional_property_messages
    )
    return annotation_value_message

  def _bare_metal_node_pool(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalNodePool."""
    kwargs = {
        'name': self._node_pool_name(args),
        'nodePoolConfig': self._node_pool_config(args),
        'displayName': getattr(args, 'display_name', None),
        'annotations': self._annotations(args),
        'bareMetalVersion': getattr(args, 'version', None),
    }

    return messages.BareMetalNodePool(**kwargs)


class NodePoolsClient(_BareMetalNodePoolsClient):
  """Client for node pools in Anthos clusters on bare metal API."""

  def __init__(self, **kwargs):
    super(NodePoolsClient, self).__init__(**kwargs)
    self._service = (
        self._client.projects_locations_bareMetalClusters_bareMetalNodePools
    )

  def List(self, location_ref, limit=None, page_size=None):
    """Lists Node Pools in the Anthos clusters on bare metal API."""
    list_req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsListRequest(
        parent=location_ref.RelativeName()
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='bareMetalNodePools',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Describe(self, resource_ref):
    """Gets a GKE On-Prem Bare Metal API node pool resource."""
    req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsGetRequest(
        name=resource_ref.RelativeName()
    )

    return self._service.Get(req)

  def Delete(self, args: parser_extensions.Namespace):
    """Deletes a GKE On-Prem Bare Metal API node pool resource."""
    kwargs = {
        'name': self._node_pool_name(args),
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'ignoreErrors': self.GetFlag(args, 'ignore_errors'),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsDeleteRequest(
        **kwargs
    )

    return self._service.Delete(req)

  def Create(self, args: parser_extensions.Namespace):
    """Creates a GKE On-Prem Bare Metal API node pool resource."""
    node_pool_ref = self._node_pool_ref(args)
    kwargs = {
        'parent': node_pool_ref.Parent().RelativeName(),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'bareMetalNodePool': self._bare_metal_node_pool(args),
        'bareMetalNodePoolId': self._node_pool_id(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsCreateRequest(
        **kwargs
    )
    return self._service.Create(req)

  def Update(self, args: parser_extensions.Namespace):
    """Updates a GKE On-Prem Bare Metal API node pool resource."""
    kwargs = {
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'name': self._node_pool_name(args),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.BARE_METAL_NODE_POOL_ARGS_TO_UPDATE_MASKS
        ),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'bareMetalNodePool': self._bare_metal_node_pool(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)

  def Enroll(self, args: parser_extensions.Namespace):
    """Enrolls an Anthos On-Prem Bare Metal API node pool resource."""
    kwargs = {
        'bareMetalNodePoolId': self._node_pool_id(args),
        'validateOnly': self.GetFlag(args, 'validate_only'),
    }
    enroll_request = messages.EnrollBareMetalNodePoolRequest(**kwargs)
    req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsEnrollRequest(
        enrollBareMetalNodePoolRequest=enroll_request,
        parent=self._node_pool_parent(args),
    )
    return self._service.Enroll(req)

  def Unenroll(self, args: parser_extensions.Namespace):
    """Unenrolls an Anthos On-Prem bare metal API node pool resource."""
    kwargs = {
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'name': self._node_pool_name(args),
        'validateOnly': self.GetFlag(args, 'validate_only'),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsUnenrollRequest(
        **kwargs
    )
    return self._service.Unenroll(req)
