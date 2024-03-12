# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Spanner database operations API helper."""

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
  poller = EmbeddedResponsePoller(
      client.projects_instances_backups_operations)
  ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='spanner.projects.instances.backups.operations')
  return waiter.WaitFor(poller, ref, message)


def Cancel(instance, backup, operation):
  """Cancel the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
          'backupsId': backup
      },
      collection='spanner.projects.instances.backups.operations')
  req = msgs.SpannerProjectsInstancesBackupsOperationsCancelRequest(
      name=ref.RelativeName())
  return client.projects_instances_backups_operations.Cancel(req)


def Get(instance, backup, operation):
  """Get the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
          'backupsId': backup
      },
      collection='spanner.projects.instances.backups.operations')
  req = msgs.SpannerProjectsInstancesBackupsOperationsGetRequest(
      name=ref.RelativeName())
  return client.projects_instances_backups_operations.Get(req)


def BuildDatabaseFilter(instance, database):
  database_ref = resources.REGISTRY.Parse(
      database,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance
      },
      collection='spanner.projects.instances.databases')
  return 'metadata.database:\"{}\"'.format(database_ref.RelativeName())


def List(instance, op_filter=None):
  """List operations on the backup."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  instance_ref = resources.REGISTRY.Parse(
      instance,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection='spanner.projects.instances')
  req = msgs.SpannerProjectsInstancesBackupOperationsListRequest(
      parent=instance_ref.RelativeName(),
      filter=op_filter)
  return list_pager.YieldFromList(
      client.projects_instances_backupOperations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


def ListGeneric(instance, backup):
  """List operations on the backup with generic LRO API."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  instance_ref = resources.REGISTRY.Parse(
      instance,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection='spanner.projects.instances')
  name = '{}/backups/{}/operations'.format(instance_ref.RelativeName(), backup)
  req = msgs.SpannerProjectsInstancesBackupsOperationsListRequest(name=name)
  return list_pager.YieldFromList(
      client.projects_instances_backups_operations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


class EmbeddedResponsePoller(waiter.CloudOperationPoller):
  """As CloudOperationPoller for polling, but uses the Operation.response."""

  def __init__(self, operation_service):
    self.operation_service = operation_service

  def GetResult(self, operation):
    return operation.response
