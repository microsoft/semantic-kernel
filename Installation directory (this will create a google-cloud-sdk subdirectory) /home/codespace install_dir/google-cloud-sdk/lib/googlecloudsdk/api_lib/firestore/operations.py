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
"""Useful commands for interacting with the Cloud Firestore Operations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.firestore import api_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources

DEFAULT_PAGE_SIZE = 100


def _GetOperationService():
  """Returns the service for interacting with the Operations service."""
  return api_utils.GetClient().projects_databases_operations


def ListOperations(project, database, limit=None, operation_filter=None):
  """Lists all of the Firestore operations.

  Args:
    project: the project to list operations for, a string.
    database: the database to list operations for, a string. Defaults to the
      default database.
    limit: the maximum number of operations to return, an integer. Defaults to
      positive infinity if unset.
    operation_filter: a filter to apply to operations, a string.

  Returns:
    a generator of Operations.
  """
  list_request = (
      api_utils.GetMessages().FirestoreProjectsDatabasesOperationsListRequest(
          filter=operation_filter,
          name='projects/{0}/databases/{1}'.format(project, database),
      )
  )
  batch_size = limit if limit else DEFAULT_PAGE_SIZE
  return list_pager.YieldFromList(
      _GetOperationService(),
      list_request,
      limit=limit,
      batch_size=batch_size,
      field='operations',
      batch_size_attribute='pageSize',
  )


def GetOperation(name):
  """Returns the google.longrunning.Operation with the given name."""
  return _GetOperationService().Get(
      api_utils.GetMessages().FirestoreProjectsDatabasesOperationsGetRequest(
          name=name
      )
  )


def CancelOperation(name):
  """Cancels the Operation with the given name."""
  return _GetOperationService().Cancel(
      api_utils.GetMessages().FirestoreProjectsDatabasesOperationsCancelRequest(
          name=name
      )
  )


def DeleteOperation(name):
  """Deletes the Operation with the given name."""
  return _GetOperationService().Delete(
      api_utils.GetMessages().FirestoreProjectsDatabasesOperationsDeleteRequest(
          name=name
      )
  )


def WaitForOperationWithName(operation_name):
  """Waits for the given Operation to complete."""
  operation = api_utils.GetMessages().GoogleLongrunningOperation(
      name=operation_name
  )

  return WaitForOperation(operation)


def WaitForOperation(operation):
  """Waits for the given Operation to complete."""
  operation_ref = resources.REGISTRY.Parse(
      operation.name,
      collection='firestore.projects.databases.operations',
      api_version=api_utils.FIRESTORE_API_VERSION)
  poller = waiter.CloudOperationPollerNoResources(
      _GetOperationService(), lambda x: x.RelativeName()
  )
  return waiter.WaitFor(
      poller, operation_ref,
      'Waiting for [{0}] to finish'.format(operation_ref.RelativeName()))
