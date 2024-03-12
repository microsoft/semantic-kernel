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
      client.projects_instances_databases_operations)
  ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='spanner.projects.instances.databases.operations')
  return waiter.WaitFor(poller, ref, message)


def Cancel(instance, database, operation):
  """Cancel the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
          'databasesId': database},
      collection='spanner.projects.instances.databases.operations')
  req = msgs.SpannerProjectsInstancesDatabasesOperationsCancelRequest(
      name=ref.RelativeName())
  return client.projects_instances_databases_operations.Cancel(req)


def Get(instance, database, operation):
  """Get the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
          'databasesId': database,
      },
      collection='spanner.projects.instances.databases.operations')
  req = msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
      name=ref.RelativeName())
  return client.projects_instances_databases_operations.Get(req)


def List(instance, database, type_filter=None):
  """List operations on the database using the generic operation list API."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      database,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance
      },
      collection='spanner.projects.instances.databases')
  req = msgs.SpannerProjectsInstancesDatabasesOperationsListRequest(
      name=ref.RelativeName()+'/operations',
      filter=type_filter)
  return list_pager.YieldFromList(
      client.projects_instances_databases_operations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


def BuildDatabaseOperationTypeFilter(op_type):
  """Builds the filter for the different database operation metadata types."""
  if op_type == 'DATABASE':
    return ''

  base_string = 'metadata.@type:type.googleapis.com/google.spanner.admin.database.v1.'
  if op_type == 'DATABASE_RESTORE':
    return '({}OptimizeRestoredDatabaseMetadata) OR ({}RestoreDatabaseMetadata)'.format(
        base_string, base_string)

  if op_type == 'DATABASE_CREATE':
    return base_string + 'CreateDatabaseMetadata'

  if op_type == 'DATABASE_UPDATE_DDL':
    return base_string + 'UpdateDatabaseDdlMetadata'

  if op_type == 'DATABASE_CHANGE_QUORUM':
    return base_string + 'DatabaseChangeQuorumMetadata'


def ListDatabaseOperations(instance, database=None, type_filter=None):
  """List database operations using the Cloud Spanner specific API."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  instance_ref = resources.REGISTRY.Parse(
      instance,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection='spanner.projects.instances')

  # When the database is passed in, use the generic list command, so no
  # operations are shown from previous incarnations of the database.
  if database:
    return List(instance, database, type_filter)

  req = msgs.SpannerProjectsInstancesDatabaseOperationsListRequest(
      parent=instance_ref.RelativeName(), filter=type_filter)
  return list_pager.YieldFromList(
      client.projects_instances_databaseOperations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


class EmbeddedResponsePoller(waiter.CloudOperationPoller):
  """As CloudOperationPoller for polling, but uses the Operation.response."""

  def __init__(self, operation_service):
    self.operation_service = operation_service

  def GetResult(self, operation):
    return operation.response
