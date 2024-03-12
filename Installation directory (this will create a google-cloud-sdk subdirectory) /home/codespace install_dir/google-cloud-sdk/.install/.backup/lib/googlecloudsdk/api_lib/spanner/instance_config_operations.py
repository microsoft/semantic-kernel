# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Spanner instance config operations API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def Get(config, operation):
  """Gets the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instanceConfigsId': config,
      },
      collection='spanner.projects.instanceConfigs.operations')
  req = msgs.SpannerProjectsInstanceConfigsOperationsGetRequest(
      name=ref.RelativeName())
  return client.projects_instanceConfigs_operations.Get(req)


def List(config, type_filter=None):
  """List operations on instanceConfig using the generic operation list API."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs')
  req = msgs.SpannerProjectsInstanceConfigsOperationsListRequest(
      name=ref.RelativeName() + '/operations', filter=type_filter)
  return list_pager.YieldFromList(
      client.projects_instanceConfigs_operations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


def Cancel(config, operation):
  """Cancel the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instanceConfigsId': config,
      },
      collection='spanner.projects.instanceConfigs.operations')
  req = msgs.SpannerProjectsInstanceConfigsOperationsCancelRequest(
      name=ref.RelativeName())
  return client.projects_instanceConfigs_operations.Cancel(req)


def Await(operation, message):
  """Wait for the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  poller = waiter.CloudOperationPoller(
      client.projects_instanceConfigs,
      client.projects_instanceConfigs_operations)
  ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='spanner.projects.instanceConfigs.operations')
  return waiter.WaitFor(poller, ref, message)


def BuildInstanceConfigOperationTypeFilter(op_type):
  """Builds the filter for the different instance config operation metadata types."""
  if op_type is None:
    return ''

  base_string = 'metadata.@type:type.googleapis.com/google.spanner.admin.instance.v1.'
  if op_type == 'INSTANCE_CONFIG_CREATE':
    return base_string + 'CreateInstanceConfigMetadata'

  if op_type == 'INSTANCE_CONFIG_UPDATE':
    return base_string + 'UpdateInstanceConfigMetadata'
