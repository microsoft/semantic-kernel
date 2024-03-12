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
"""Utilities for node pool resources in Anthos standalone clusters on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages as protorpc_message
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import standalone_clusters
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages_module


class _StandaloneNodePoolsClient(standalone_clusters.StandaloneClustersClient):
  """Base class for GKE OnPrem Bare Metal Standalone Node Pool API clients."""

  def _node_taints(self, args: parser_extensions.Namespace):
    """Constructs proto message NodeTaint."""
    taint_messages = []
    node_taints = getattr(args, 'node_taints', {})
    if not node_taints:
      return []

    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages_module.NodeTaint(**taint_object))

    return taint_messages

  def _node_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message LabelsValue."""
    node_labels = getattr(args, 'node_labels', {})
    additional_property_messages = []
    if not node_labels:
      return None

    for key, value in node_labels.items():
      additional_property_messages.append(
          messages_module.BareMetalStandaloneNodePoolConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = (
        messages_module.BareMetalStandaloneNodePoolConfig.LabelsValue(
            additionalProperties=additional_property_messages
        )
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
    """Constructs proto message BareMetalStandaloneNodeConfig."""
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

    return messages_module.BareMetalStandaloneNodeConfig(**kwargs)

  def _node_config_labels(self, labels):
    """Constructs proto message LabelsValue."""
    additional_property_messages = []
    if not labels:
      return None

    for key, value in labels.items():
      additional_property_messages.append(
          messages_module.BareMetalStandaloneNodeConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = (
        messages_module.BareMetalStandaloneNodeConfig.LabelsValue(
            additionalProperties=additional_property_messages
        )
    )

    return labels_value_message

  def parse_standalone_node_labels(self, node_labels):
    """Validates and parses a standalone node label object.

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
          messages_module.BareMetalStandaloneNodeConfig.LabelsValue.AdditionalProperty(
              key=key_val_pair[0], value=key_val_pair[1]
          )
      )

    labels_value_message = (
        messages_module.BareMetalStandaloneNodeConfig.LabelsValue(
            additionalProperties=additional_property_messages
        )
    )

    return labels_value_message

  # TODO(b/290071347): Reuse the function in standalone cluster client class
  def standalone_node_config(self, node_config_args):
    """Constructs proto message BareMetalStandaloneNodeConfig."""
    kwargs = {
        'nodeIp': node_config_args.get('node-ip', ''),
        'labels': self.parse_standalone_node_labels(node_config_args),
    }

    return self._set_config_if_exists(
        messages_module.BareMetalStandaloneNodeConfig, kwargs
    )

  def _node_configs_from_flag(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    node_configs = []
    node_config_flag_value = getattr(args, 'node_configs', None)
    if node_config_flag_value:
      for node_config in node_config_flag_value:
        node_configs.append(self.standalone_node_config(node_config))

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
      return messages_module.BareMetalStandaloneKubeletConfig(**kwargs)
    return None

  def _node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneNodePoolConfig."""
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
      return messages_module.BareMetalStandaloneNodePoolConfig(**kwargs)

    return None

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    annotations = getattr(args, 'annotations', {})
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          messages_module.BareMetalStandaloneNodePool.AnnotationsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    annotation_value_message = (
        messages_module.BareMetalStandaloneNodePool.AnnotationsValue(
            additionalProperties=additional_property_messages
        )
    )
    return annotation_value_message

  def _bare_metal_standalone_node_pool(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneNodePool."""
    kwargs = {
        'name': self._node_pool_name(args),
        'nodePoolConfig': self._node_pool_config(args),
        'displayName': getattr(args, 'display_name', None),
        'annotations': self._annotations(args),
    }

    return messages_module.BareMetalStandaloneNodePool(**kwargs)


class StandaloneNodePoolsClient(_StandaloneNodePoolsClient):
  """Client for node pools in Anthos clusters on bare metal standalone API."""

  def __init__(self, **kwargs):
    super(StandaloneNodePoolsClient, self).__init__(**kwargs)
    self._service = (
        self._client.projects_locations_bareMetalStandaloneClusters_bareMetalStandaloneNodePools
    )

  def List(
      self,
      location_ref: protorpc_message.Message,
      limit=None,
      page_size=None,
  ) -> protorpc_message.Message:
    """Lists Node Pools in the Anthos clusters on bare metal standalone API."""
    list_req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsListRequest(
        parent=location_ref.RelativeName()
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='bareMetalStandaloneNodePools',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Describe(self, resource_ref):
    """Gets a GKE On-Prem Bare Metal API standalone node pool resource."""
    req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsGetRequest(
        name=resource_ref.RelativeName()
    )

    return self._service.Get(req)

  def Enroll(
      self, args: parser_extensions.Namespace
  ) -> protorpc_message.Message:
    """Enrolls an Anthos On-Prem Bare Metal API standalone node pool resource.

    Args:
      args: parser_extensions.Namespace, known args specified on the command
        line.

    Returns:
      (Operation) The response message.
    """
    req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsEnrollRequest(
        enrollBareMetalStandaloneNodePoolRequest=messages_module.EnrollBareMetalStandaloneNodePoolRequest(
            bareMetalStandaloneNodePoolId=self._standalone_node_pool_id(args),
            validateOnly=self.GetFlag(args, 'validate_only'),
        ),
        parent=self._standalone_node_pool_parent(args),
    )

    return self._service.Enroll(req)

  def Unenroll(
      self, args: parser_extensions.Namespace
  ) -> protorpc_message.Message:
    """Unenrolls an Anthos On-Prem bare metal API standalone node pool resource.

    Args:
      args: parser_extensions.Namespace, known args specified on the command
        line.

    Returns:
      (Operation) The response message.
    """
    kwargs = {
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'name': self._standalone_node_pool_name(args),
        'validateOnly': self.GetFlag(args, 'validate_only'),
    }
    req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsUnenrollRequest(
        **kwargs
    )
    return self._service.Unenroll(req)

  def Delete(
      self, args: parser_extensions.Namespace
  ) -> protorpc_message.Message:
    """Deletes a GKE On-Prem Bare Metal API standalone node pool resource."""
    kwargs = {
        'name': self._standalone_node_pool_name(args),
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'ignoreErrors': self.GetFlag(args, 'ignore_errors'),
    }
    req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsDeleteRequest(
        **kwargs
    )

    return self._service.Delete(req)

  def Create(self, args: parser_extensions.Namespace):
    """Creates a GKE On-Prem Bare Metal API standalone node pool resource."""
    node_pool_ref = self._node_pool_ref(args)
    kwargs = {
        'parent': node_pool_ref.Parent().RelativeName(),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'bareMetalStandaloneNodePool': self._bare_metal_standalone_node_pool(
            args
        ),
        'bareMetalStandaloneNodePoolId': self._standalone_node_pool_id(args),
    }
    req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsCreateRequest(
        **kwargs
    )
    return self._service.Create(req)

  def Update(
      self, args: parser_extensions.Namespace
  ) -> protorpc_message.Message:
    """Updates a GKE On-Prem Bare Metal API standalone node pool resource."""
    req = messages_module.GkeonpremProjectsLocationsBareMetalStandaloneClustersBareMetalStandaloneNodePoolsPatchRequest(
        allowMissing=self.GetFlag(args, 'allow_missing'),
        name=self._standalone_node_pool_name(args),
        updateMask=update_mask.get_update_mask(
            args,
            update_mask.BARE_METAL_STANDALONE_NODE_POOL_ARGS_TO_UPDATE_MASKS,
        ),
        validateOnly=self.GetFlag(args, 'validate_only'),
        bareMetalStandaloneNodePool=self._bare_metal_standalone_node_pool(
            args
        ),
    )
    return self._service.Patch(req)
