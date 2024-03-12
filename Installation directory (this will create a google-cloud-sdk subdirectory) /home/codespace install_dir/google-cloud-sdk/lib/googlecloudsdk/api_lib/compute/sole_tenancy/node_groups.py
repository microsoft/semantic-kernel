# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Node group api client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils as compute_util
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import util
from six.moves import map


class NodeGroupsClient(object):
  """Client for node groups service in the GCE API."""

  def __init__(self, client, messages, resources):
    self.client = client
    self.messages = messages
    self.resources = resources
    self._service = self.client.nodeGroups

  def SetNodeTemplate(self, node_group_ref, node_template):
    """Sets the node template field on the node group."""
    node_template_ref = util.ParseNodeTemplate(
        self.resources,
        node_template,
        project=node_group_ref.project,
        region=compute_util.ZoneNameToRegionName(node_group_ref.zone))
    set_request = self.messages.NodeGroupsSetNodeTemplateRequest(
        nodeTemplate=node_template_ref.RelativeName())
    request = self.messages.ComputeNodeGroupsSetNodeTemplateRequest(
        nodeGroupsSetNodeTemplateRequest=set_request,
        nodeGroup=node_group_ref.Name(),
        project=node_group_ref.project,
        zone=node_group_ref.zone)
    return self._service.SetNodeTemplate(request)

  def AddNodes(self, node_group_ref, additional_node_count):
    request = self.messages.ComputeNodeGroupsAddNodesRequest(
        nodeGroupsAddNodesRequest=self.messages.NodeGroupsAddNodesRequest(
            additionalNodeCount=additional_node_count),
        nodeGroup=node_group_ref.Name(),
        project=node_group_ref.project,
        zone=node_group_ref.zone)
    return self._service.AddNodes(request)

  def DeleteNodes(self, node_group_ref, nodes):
    request = self.messages.ComputeNodeGroupsDeleteNodesRequest(
        nodeGroupsDeleteNodesRequest=self.messages.NodeGroupsDeleteNodesRequest(
            nodes=nodes),
        nodeGroup=node_group_ref.Name(),
        project=node_group_ref.project,
        zone=node_group_ref.zone)
    return self._service.DeleteNodes(request)

  def Patch(self, node_group_ref, args):
    """Sets the autoscaling policy on a node group."""
    autoscaling_policy_ref = util.BuildAutoscaling(args, self.messages)
    set_request = self.messages.NodeGroup(
        autoscalingPolicy=autoscaling_policy_ref)
    request = self.messages.ComputeNodeGroupsPatchRequest(
        nodeGroupResource=set_request,
        nodeGroup=node_group_ref.Name(),
        project=node_group_ref.project,
        zone=node_group_ref.zone)
    return self._service.Patch(request)

  def UpdateShareSetting(self, node_group_ref, share_setting):
    """Sets the share setting on a node group."""
    share_setting_ref = util.BuildShareSettings(self.messages, share_setting)
    set_request = self.messages.NodeGroup(shareSettings=share_setting_ref)
    request = self.messages.ComputeNodeGroupsPatchRequest(
        nodeGroupResource=set_request,
        nodeGroup=node_group_ref.Name(),
        project=node_group_ref.project,
        zone=node_group_ref.zone)
    return self._service.Patch(request)

  def _GetOperationsRef(self, operation):
    return self.resources.Parse(operation.selfLink,
                                collection='compute.zoneOperations')

  def _WaitForResult(self, operation_poller, operation_ref, message):
    if operation_ref:
      return waiter.WaitFor(operation_poller, operation_ref, message)
    return None

  def Update(self,
             node_group_ref,
             node_template=None,
             additional_node_count=None,
             delete_nodes=None,
             autoscaling_policy_args=None,
             share_setting_args=None):
    """Updates a Compute Node Group."""
    set_node_template_ref = None
    add_nodes_ref = None
    delete_nodes_ref = None
    autoscaling_policy_ref = None
    share_settings_ref = None

    if node_template:
      operation = self.SetNodeTemplate(node_group_ref, node_template)
      set_node_template_ref = self._GetOperationsRef(operation)

    if additional_node_count:
      operation = self.AddNodes(node_group_ref, additional_node_count)
      add_nodes_ref = self._GetOperationsRef(operation)

    if delete_nodes:
      operation = self.DeleteNodes(node_group_ref, delete_nodes)
      delete_nodes_ref = self._GetOperationsRef(operation)

    if autoscaling_policy_args:
      operation = self.Patch(node_group_ref, autoscaling_policy_args)
      autoscaling_policy_ref = self._GetOperationsRef(operation)

    if share_setting_args:
      operation = self.UpdateShareSetting(node_group_ref, share_setting_args)
      share_settings_ref = self._GetOperationsRef(operation)

    node_group_name = node_group_ref.Name()
    operation_poller = poller.Poller(self._service)
    result = None
    result = self._WaitForResult(
        operation_poller, set_node_template_ref,
        'Setting node template on [{0}] to [{1}].'.format(
            node_group_name, node_template)) or result
    result = self._WaitForResult(
        operation_poller, add_nodes_ref,
        'Adding [{0}] nodes to [{1}].'.format(
            additional_node_count, node_group_name)) or result
    deleted_nodes_str = ','.join(map(str, delete_nodes or []))
    result = self._WaitForResult(
        operation_poller, delete_nodes_ref,
        'Deleting nodes [{0}] in [{1}].'.format(
            deleted_nodes_str, node_group_name)) or result

    autoscaling_policy_str_list = []
    if autoscaling_policy_args:
      if autoscaling_policy_args.autoscaler_mode:
        mode_str = 'autoscaler-mode={0}'.format(
            autoscaling_policy_args.autoscaler_mode)
        autoscaling_policy_str_list.append(mode_str)
      if autoscaling_policy_args.IsSpecified('min_nodes'):
        min_str = 'min-nodes={0}'.format(autoscaling_policy_args.min_nodes)
        autoscaling_policy_str_list.append(min_str)
      if autoscaling_policy_args.IsSpecified('max_nodes'):
        max_str = 'max-nodes={0}'.format(autoscaling_policy_args.max_nodes)
        autoscaling_policy_str_list.append(max_str)
    autoscaling_policy_str = ','.join(autoscaling_policy_str_list)
    result = self._WaitForResult(
        operation_poller, autoscaling_policy_ref,
        'Updating autoscaling policy on [{0}] to [{1}].'.format(
            node_group_name, autoscaling_policy_str)) or result
    share_setting_str_list = []
    if share_setting_args:
      type_str = 'share-setting={0}'.format(share_setting_args.share_setting)
      share_setting_str_list.append(type_str)
      if share_setting_args.share_with:
        with_str = 'share-with={0}'.format(','.join(
            share_setting_args.share_with))
        share_setting_str_list.append(with_str)
    share_setting_str = ','.join(share_setting_str_list)
    result = self._WaitForResult(
        operation_poller, share_settings_ref,
        'Updating share setting on [{0}] to [{1}].'.format(
            node_group_name, share_setting_str)) or result
    return result
