# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Spanner instance operations API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def Await(operation, message):
  """Wait for the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  poller = waiter.CloudOperationPoller(
      client.projects_instances,
      client.projects_instances_operations)
  ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='spanner.projects.instances.operations')
  return waiter.WaitFor(poller, ref, message)


def Cancel(instance, operation):
  """Cancel the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance
      },
      collection='spanner.projects.instances.operations')
  req = msgs.SpannerProjectsInstancesOperationsCancelRequest(
      name=ref.RelativeName())
  return client.projects_instances_operations.Cancel(req)


def Get(instance, operation):
  """Get the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance
      },
      collection='spanner.projects.instances.operations')
  req = msgs.SpannerProjectsInstancesOperationsGetRequest(
      name=ref.RelativeName())
  return client.projects_instances_operations.Get(req)


def List(instance):
  """List operations on the instance."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      instance,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instances')
  req = msgs.SpannerProjectsInstancesOperationsListRequest(
      name=ref.RelativeName()+'/operations')
  return list_pager.YieldFromList(
      client.projects_instances_operations,
      req,
      field='operations',
      batch_size_attribute='pageSize')
