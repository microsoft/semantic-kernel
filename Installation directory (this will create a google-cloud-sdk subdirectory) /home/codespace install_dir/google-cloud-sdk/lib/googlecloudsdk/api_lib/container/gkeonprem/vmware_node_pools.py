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
"""Utilities for node pool resources in Anthos clusters on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Generator

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class NodePoolsClient(client.ClientBase):
  """Client for node pools in Anthos clusters on VMware API."""

  def __init__(self, **kwargs):
    super(NodePoolsClient, self).__init__(**kwargs)
    self._service = (
        self._client.projects_locations_vmwareClusters_vmwareNodePools
    )

  def List(
      self, args: parser_extensions.Namespace
  ) -> Generator[messages.VmwareNodePool, None, None]:
    """Lists Node Pools in the Anthos clusters on VMware API."""
    list_req = messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsListRequest(
        parent=self._user_cluster_name(args)
    )
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='vmwareNodePools',
        batch_size=flags.Get(args, 'page_size'),
        limit=flags.Get(args, 'limit'),
        batch_size_attribute='pageSize',
    )

  def Delete(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Deletes a gkeonprem node pool API resource."""
    kwargs = {
        'allowMissing': flags.Get(args, 'allow_missing'),
        'etag': flags.Get(args, 'etag'),
        'name': self._node_pool_name(args),
        'validateOnly': flags.Get(args, 'validate_only'),
        'ignoreErrors': flags.Get(args, 'ignore_errors'),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsDeleteRequest(
        **kwargs
    )
    return self._service.Delete(req)

  def Create(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Creates a gkeonprem node pool API resource."""
    node_pool_ref = self._node_pool_ref(args)
    kwargs = {
        'parent': node_pool_ref.Parent().RelativeName(),
        'validateOnly': flags.Get(args, 'validate_only'),
        'vmwareNodePool': self._vmware_node_pool(args),
        'vmwareNodePoolId': self._node_pool_id(args),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsCreateRequest(
        **kwargs
    )
    return self._service.Create(req)

  def Update(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Updates a gkeonprem node pool API resource."""
    kwargs = {
        'allowMissing': flags.Get(args, 'allow_missing'),
        'name': self._node_pool_name(args),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.VMWARE_NODE_POOL_ARGS_TO_UPDATE_MASKS
        ),
        'validateOnly': flags.Get(args, 'validate_only'),
        'vmwareNodePool': self._vmware_node_pool(args),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)

  def Enroll(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Enrolls an Anthos on VMware node pool API resource."""
    enroll_vmware_node_pool_request = messages.EnrollVmwareNodePoolRequest(
        vmwareNodePoolId=self._node_pool_id(args),
    )
    req = messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsEnrollRequest(
        enrollVmwareNodePoolRequest=enroll_vmware_node_pool_request,
        parent=self._node_pool_parent(args),
    )
    return self._service.Enroll(req)

  def Unenroll(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Unenrolls an Anthos on VMware node pool API resource."""
    kwargs = {
        'allowMissing': flags.Get(args, 'allow_missing'),
        'etag': flags.Get(args, 'etag'),
        'name': self._node_pool_name(args),
        'validateOnly': flags.Get(args, 'validate_only'),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsUnenrollRequest(
        **kwargs
    )
    return self._service.Unenroll(req)

  def _vmware_node_pool(
      self, args: parser_extensions.Namespace
  ) -> messages.VmwareNodePool:
    """Constructs proto message VmwareNodePool."""
    kwargs = {
        'name': self._node_pool_name(args),
        'displayName': flags.Get(args, 'display_name'),
        'annotations': self._annotations(args),
        'config': self._vmware_node_config(args),
        'onPremVersion': flags.Get(args, 'version'),
        'nodePoolAutoscaling': self._vmware_node_pool_autoscaling_config(args),
    }
    return messages.VmwareNodePool(**kwargs)

  def _enable_load_balancer(self, args: parser_extensions.Namespace):
    if flags.Get(args, 'enable_load_balancer'):
      return True
    if flags.Get(args, 'disable_load_balancer'):
      return False
    return None

  def _node_taints(self, args: parser_extensions.Namespace):
    taint_messages = []
    node_taints = flags.Get(args, 'node_taints', {})
    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))
    return taint_messages

  def _labels_value(
      self, args: parser_extensions.Namespace
  ) -> messages.VmwareNodeConfig.LabelsValue:
    """Constructs proto message LabelsValue."""
    node_labels = flags.Get(args, 'node_labels', {})
    additional_property_messages = []
    if not node_labels:
      return None

    for key, value in node_labels.items():
      additional_property_messages.append(
          messages.VmwareNodeConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.VmwareNodeConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _vmware_node_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareNodeConfig."""
    kwargs = {
        'cpus': flags.Get(args, 'cpus'),
        'memoryMb': flags.Get(args, 'memory'),
        'replicas': flags.Get(args, 'replicas'),
        'imageType': flags.Get(args, 'image_type'),
        'image': flags.Get(args, 'image'),
        'bootDiskSizeGb': flags.Get(args, 'boot_disk_size'),
        'taints': self._node_taints(args),
        'labels': self._labels_value(args),
        'vsphereConfig': self._vsphere_config(args),
        'enableLoadBalancer': self._enable_load_balancer(args),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareNodeConfig(**kwargs)
    return None

  def _vsphere_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareVsphereConfig."""
    if 'vsphere_config' not in args.GetSpecifiedArgsDict():
      return None

    kwargs = {
        'datastore': args.vsphere_config.get('datastore', None),
        'storagePolicyName': args.vsphere_config.get(
            'storage-policy-name', None
        ),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareVsphereConfig(**kwargs)
    return None

  def _vmware_node_pool_autoscaling_config(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message VmwareNodePoolAutoscalingConfig."""
    kwargs = {
        'minReplicas': flags.Get(args, 'min_replicas'),
        'maxReplicas': flags.Get(args, 'max_replicas'),
    }
    if any(kwargs.values()):
      return messages.VmwareNodePoolAutoscalingConfig(**kwargs)
    return None

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    annotations = flags.Get(args, 'annotations', {})
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          messages.VmwareNodePool.AnnotationsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    annotation_value_message = messages.VmwareNodePool.AnnotationsValue(
        additionalProperties=additional_property_messages
    )
    return annotation_value_message
