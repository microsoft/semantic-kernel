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
"""Helpers for the container node pool related commands."""

from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources


def GetNodePoolReference(args):
  """Get edgecontainer node pool resources.

  Args:
    args: command line arguments.

  Returns:
    edgecontainer node pool resources.
  """
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.node_pool.Parse().RelativeName(),
      collection='edgecontainer.projects.locations.clusters.nodePools',
  )


def GetNodePoolGetRequest(args, release_track):
  """Get node pool get request message.

  Args:
    args: comand line arguments.
    release_track: release track of the command.

  Returns:
    message obj, node pool get request message.
  """
  messages = util.GetMessagesModule(release_track)
  req = messages.EdgecontainerProjectsLocationsClustersNodePoolsGetRequest(
      name=args.CONCEPTS.node_pool.Parse().RelativeName(),
  )
  return req


def GetNodePoolCreateRequest(args, release_track):
  """Get node pool create request message.

  Args:
    args: comand line arguments.
    release_track: release track of the command.

  Returns:
    message obj, node pool create request message.
  """
  messages = util.GetMessagesModule(release_track)
  node_pool_ref = GetNodePoolReference(args)
  req = messages.EdgecontainerProjectsLocationsClustersNodePoolsCreateRequest(
      nodePool=messages.NodePool(),
      nodePoolId=node_pool_ref.nodePoolsId,
      parent=node_pool_ref.Parent().RelativeName(),
  )
  PopulateNodePoolCreateMessage(req, messages, args)
  return req


def GetNodePoolUpdateRequest(args, release_track, existing_node_pool):
  """Get node pool update request message.

  Args:
    args: comand line arguments.
    release_track: release track of the command.
    existing_node_pool: existing node pool.

  Returns:
    message obj, node pool update request message.
  """
  messages = util.GetMessagesModule(release_track)
  req = messages.EdgecontainerProjectsLocationsClustersNodePoolsPatchRequest(
      name=args.CONCEPTS.node_pool.Parse().RelativeName(),
      nodePool=messages.NodePool(),
  )
  update_mask_pieces = []
  PopulateNodePoolUpdateMessage(
      req, messages, args, update_mask_pieces, existing_node_pool
  )
  req.updateMask = ','.join(update_mask_pieces)
  return req


def PopulateNodePoolCreateMessage(req, messages, args):
  """Fill the node pool message from command arguments.

  Args:
    req: create node pool request message.
    messages: message module of edgecontainer node pool.
    args: command line arguments.
  """
  req.nodePool.nodeCount = int(args.node_count)
  req.nodePool.nodeLocation = args.node_location
  if flags.FlagIsExplicitlySet(args, 'machine_filter'):
    req.nodePool.machineFilter = args.machine_filter
  if flags.FlagIsExplicitlySet(args, 'local_disk_kms_key'):
    req.nodePool.localDiskEncryption = messages.LocalDiskEncryption()
    req.nodePool.localDiskEncryption.kmsKey = args.local_disk_kms_key
  if flags.FlagIsExplicitlySet(args, 'labels'):
    req.nodePool.labels = messages.NodePool.LabelsValue()
    req.nodePool.labels.additionalProperties = []
    for key, value in args.labels.items():
      v = messages.NodePool.LabelsValue.AdditionalProperty()
      v.key = key
      v.value = value
      req.nodePool.labels.additionalProperties.append(v)
  if flags.FlagIsExplicitlySet(args, 'node_labels'):
    req.nodePool.nodeConfig = messages.NodeConfig()
    req.nodePool.nodeConfig.labels = messages.NodeConfig.LabelsValue()
    req.nodePool.nodeConfig.labels.additionalProperties = []
    for key, value in args.node_labels.items():
      v = messages.NodeConfig.LabelsValue.AdditionalProperty()
      v.key = key
      v.value = value
      req.nodePool.nodeConfig.labels.additionalProperties.append(v)


def PopulateNodePoolUpdateMessage(
    req, messages, args, update_mask_pieces, existing_node_pool
):
  """Fill the node pool message from command arguments.

  Args:
    req: update node pool request message.
    messages: message module of edgecontainer node pool.
    args: command line arguments.
    update_mask_pieces: update mask pieces.
    existing_node_pool: existing node pool.
  """
  if flags.FlagIsExplicitlySet(args, 'machine_filter'):
    update_mask_pieces.append('machineFilter')
    req.nodePool.machineFilter = args.machine_filter
  if flags.FlagIsExplicitlySet(args, 'node_count'):
    update_mask_pieces.append('nodeCount')
    req.nodePool.nodeCount = int(args.node_count)
  add_labels = labels_util.GetUpdateLabelsDictFromArgs(args)
  remove_labels = labels_util.GetRemoveLabelsListFromArgs(args)
  value_type = messages.NodePool.LabelsValue
  label_update_result = labels_util.Diff(
      additions=add_labels, subtractions=remove_labels, clear=args.clear_labels
  ).Apply(value_type, existing_node_pool.labels)
  if label_update_result.needs_update:
    update_mask_pieces.append('labels')
    req.nodePool.labels = label_update_result.labels
  if flags.FlagIsExplicitlySet(args, 'node_labels'):
    update_mask_pieces.append('nodeConfig.labels')
    req.nodePool.nodeConfig = messages.NodeConfig()
    req.nodePool.nodeConfig.labels = messages.NodeConfig.LabelsValue()
    req.nodePool.nodeConfig.labels.additionalProperties = []
    for key, value in args.node_labels.items():
      v = messages.NodeConfig.LabelsValue.AdditionalProperty()
      v.key = key
      v.value = value
      req.nodePool.nodeConfig.labels.additionalProperties.append(v)
